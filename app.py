"""
FastAPI server for chatting with Insurance Agents
"""
import asyncio
import uuid
import json
import time
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import List, Optional

from src.db.repository import PolicyRepository
from src.db.connection import DatabaseConnection
from src.agents.intake_agent import IntakeAgent
from src.agents.quotation_agent import QuotationAgent
from src.agents.payment_agent import PaymentAgent
from src.agents.issuance_agent import IssuanceAgent
from agents import Runner

load_dotenv()

app = FastAPI(title="aseguraOpen - Insurance Agents")

# Get DB query delay from env
DB_QUERY_DELAY = float(os.getenv("DB_QUERY_DELAY", "0"))

# Health check endpoint (before startup)
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}

# ========== OpenAI Chat Completions API Compatible Endpoints ==========

class Message(BaseModel):
    """Chat message compatible with OpenAI Chat Completions format"""
    role: str  # "user", "assistant", "system", "developer"
    content: str

class ChatCompletionRequest(BaseModel):
    """Request model compatible with OpenAI Chat Completions API"""
    messages: List[Message]
    model: str = "aseguraopen"
    temperature: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    session_id: Optional[str] = None  # Custom field for tracking

class ChatCompletionChoice(BaseModel):
    """Choice object in chat completion response"""
    index: int
    message: Message
    finish_reason: str = "stop"

class ChatCompletionUsage(BaseModel):
    """Token usage info"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class ChatCompletionResponse(BaseModel):
    """Response compatible with OpenAI Chat Completions API"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: ChatCompletionUsage

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI Chat Completions API compatible endpoint.
    Compatible with OpenAI client libraries and tools.
    """
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        session = PolicyRepository.get_session(session_id)
        
        if not session:
            # Create new policy and session
            policy = PolicyRepository.create_policy("intake")
            PolicyRepository.create_session(session_id, policy.id)
            policy_id = policy.id
        else:
            policy_id = session["policy_id"]
        
        # Get the last user message
        user_message = next(
            (m.content for m in reversed(request.messages) if m.role == "user"),
            None
        )
        
        if not user_message:
            raise HTTPException(status_code=400, detail="No user message provided")
        
        # Add delay if configured
        if DB_QUERY_DELAY > 0:
            await asyncio.sleep(DB_QUERY_DELAY)
        
        # Get current policy state
        policy = PolicyRepository.get_policy(policy_id)
        client_data = PolicyRepository.get_client_data(policy_id)
        vehicle_data = PolicyRepository.get_vehicle_data(policy_id)
        
        # Determine which agent to use based on policy state
        current_state = policy.state
        agent = None
        
        if current_state == "intake":
            agent = IntakeAgent.create_agent()
        elif current_state == "loaded":
            agent = QuotationAgent.create_agent()
        elif current_state == "quotation":
            agent = QuotationAgent.create_agent()
        elif current_state == "payment":
            agent = PaymentAgent.create_agent()
        elif current_state == "issued":
            agent = IssuanceAgent.create_agent()
        elif current_state == "completed":
            response_text = "✅ ¡Tu póliza ya está completada! Si necesitas hacer cambios, contáctanos."
        else:
            agent = IntakeAgent.create_agent()
        
        # Build conversation history for context
        session_messages = session.get("messages", [])
        conversation_history = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}" 
            for msg in session_messages
        ])
        
        # Build system context based on current state
        system_context = f"""CONTEXTO ACTUAL DE LA PÓLIZA:
- Policy ID: {policy_id}
- Estado: {policy.state}
- Tipo de Seguro: {policy.insurance_type or "No especificado"}
- Cliente: {client_data.name if client_data else "No completado"}
- Email: {client_data.email if client_data else "N/A"}
- Teléfono: {client_data.phone if client_data else "N/A"}
- Vehículo: {f"{vehicle_data.make} {vehicle_data.model}" if vehicle_data else "No ingresado"}

HISTORIAL DE CONVERSACIÓN:
{conversation_history if conversation_history else 'No hay mensajes previos'}

NUEVO MENSAJE DEL CLIENTE:
{user_message}"""
        
        # Add user message to session
        messages = session.get("messages", [])
        messages.append({
            "role": "user",
            "content": user_message
        })
        PolicyRepository.update_session_messages(session_id, messages)
        
        # Add delay if configured
        if DB_QUERY_DELAY > 0:
            await asyncio.sleep(DB_QUERY_DELAY)
        
        # Run the appropriate agent based on state
        if agent is not None:
            result = await Runner.run(agent, system_context)
            response_text = str(result.final_output)
        # else response_text already set for completed state
        
        # Add agent response to session
        messages.append({
            "role": "assistant",
            "content": response_text
        })
        PolicyRepository.update_session_messages(session_id, messages)
        
        # Add delay if configured
        if DB_QUERY_DELAY > 0:
            await asyncio.sleep(DB_QUERY_DELAY)
        
        # Build response in OpenAI format
        completion_id = f"chatcmpl-{uuid.uuid4().hex[:16]}"
        
        return ChatCompletionResponse(
            id=completion_id,
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=Message(
                        role="assistant",
                        content=response_text
                    ),
                    finish_reason="stop"
                )
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=len(user_message.split()),
                completion_tokens=len(response_text.split()),
                total_tokens=len(user_message.split()) + len(response_text.split())
            )
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/completions")
async def chat_completions_legacy(request: ChatCompletionRequest):
    """Legacy endpoint without /v1 prefix for compatibility"""
    return await chat_completions(request)

@app.on_event("startup")
async def startup_event():
    """Initialize DB on startup"""
    try:
        print("Starting database initialization...")
        DatabaseConnection.get_connection()
        print("Database connection established")
        try:
            PolicyRepository.seed_quotation_templates()
            print("Quotation templates seeded")
        except Exception as e:
            print(f"Warning: Could not seed templates: {e}")
        print("Database initialization completed")
    except Exception as e:
        print(f"ERROR during startup: {e}")
        import traceback
        traceback.print_exc()
        # Don't re-raise - let the app continue to serve requests

class MessageRequest(BaseModel):
    message: str

class ChatSession(BaseModel):
    policy_id: str
    messages: list = []

@app.post("/api/chat/start")
async def start_chat():
    """Start a new chat session"""
    try:
        policy = PolicyRepository.create_policy("intake")
        session_id = str(uuid.uuid4())
        
        # Save session to database instead of in-memory dict
        PolicyRepository.create_session(session_id, policy.id)
        
        # Add delay to prevent rate limiting
        if DB_QUERY_DELAY > 0:
            await asyncio.sleep(DB_QUERY_DELAY)
        
        return {
            "session_id": session_id,
            "policy_id": policy.id,
            "message": "Iniciando sesión... Por favor espera un momento."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/{session_id}/restore")
async def restore_chat(session_id: str):
    """Restore an existing chat session"""
    try:
        session = PolicyRepository.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        policy_id = session["policy_id"]
        
        # Get current policy state
        policy = PolicyRepository.get_policy(policy_id)
        client_data = PolicyRepository.get_client_data(policy_id)
        vehicle_data = PolicyRepository.get_vehicle_data(policy_id)
        quotations = PolicyRepository.get_quotations(policy_id)
        
        # Add delay to prevent rate limiting
        if DB_QUERY_DELAY > 0:
            await asyncio.sleep(DB_QUERY_DELAY)
        
        return {
            "session_id": session_id,
            "policy_id": policy_id,
            "policy_state": policy.state,
            "intention_confirmed": policy.intention,
            "insurance_type": policy.insurance_type,
            "client_saved": client_data is not None,
            "client_name": client_data.name if client_data else None,
            "client_email": client_data.email if client_data else None,
            "client_phone": client_data.phone if client_data else None,
            "vehicle_saved": vehicle_data is not None,
            "vehicle_make": vehicle_data.make if vehicle_data else None,
            "vehicle_model": vehicle_data.model if vehicle_data else None,
            "quotations": quotations,
            "messages": session["messages"],
            "message": "✅ Sesión restaurada. Continuamos donde nos quedamos."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/{session_id}/restart")
async def restart_chat(session_id: str):
    """Restart/reset a chat session - clears messages but keeps policy"""
    try:
        session = PolicyRepository.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Clear messages but keep the session
        PolicyRepository.update_session_messages(session_id, [])
        
        policy_id = session["policy_id"]
        policy = PolicyRepository.get_policy(policy_id)
        
        # Add delay to prevent rate limiting
        if DB_QUERY_DELAY > 0:
            await asyncio.sleep(DB_QUERY_DELAY)
        
        return {
            "session_id": session_id,
            "policy_id": policy_id,
            "message": "🔄 Conversación reiniciada. Comencemos de nuevo."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/{session_id}/message")
async def send_message(session_id: str, request: MessageRequest):
    """Send a message to the agent"""
    try:
        session = PolicyRepository.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        policy_id = session["policy_id"]
        
        # Add delay to prevent rate limiting
        if DB_QUERY_DELAY > 0:
            await asyncio.sleep(DB_QUERY_DELAY)
        
        # Get current policy state
        policy = PolicyRepository.get_policy(policy_id)
        client_data = PolicyRepository.get_client_data(policy_id)
        vehicle_data = PolicyRepository.get_vehicle_data(policy_id)
        
        # Determine which agent to use based on policy state
        current_state = policy.state
        agent = None
        
        if current_state == "intake":
            agent = IntakeAgent.create_agent()
        elif current_state == "loaded":
            agent = QuotationAgent.create_agent()
        elif current_state == "quotation":
            agent = QuotationAgent.create_agent()
        elif current_state == "payment":
            agent = PaymentAgent.create_agent()
        elif current_state == "issued":
            agent = IssuanceAgent.create_agent()
        elif current_state == "completed":
            return {
                "response": "✅ ¡Tu póliza ya está completada! Si necesitas hacer cambios, contáctanos.",
                "policy_state": "completed",
                "messages": session["messages"]
            }
        else:
            raise HTTPException(status_code=500, detail=f"Unknown policy state: {current_state}")
        
        # Build conversation history for context
        conversation_history = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}" 
            for msg in session["messages"]
        ])
        
        # Build system context based on current state
        system_context = f"""CONTEXTO ACTUAL DE LA PÓLIZA:
- Policy ID: {policy_id}
- Estado: {policy.state}
- Tipo de Seguro: {policy.insurance_type or "No especificado"}
- Cliente: {client_data.name if client_data else "No completado"}
- Email: {client_data.email if client_data else "N/A"}
- Teléfono: {client_data.phone if client_data else "N/A"}
- Vehículo: {f"{vehicle_data.make} {vehicle_data.model}" if vehicle_data else "No ingresado"}

HISTORIAL DE CONVERSACIÓN:
{conversation_history if conversation_history else 'No hay mensajes previos'}

NUEVO MENSAJE DEL CLIENTE:
{request.message}"""
        
        # Add user message to session
        messages = session["messages"]
        messages.append({
            "role": "user",
            "content": request.message
        })
        PolicyRepository.update_session_messages(session_id, messages)
        
        # Add delay to prevent rate limiting
        if DB_QUERY_DELAY > 0:
            await asyncio.sleep(DB_QUERY_DELAY)
        
        # Run the appropriate agent based on state
        if agent is None:
            raise HTTPException(status_code=500, detail="No agent could be selected")
        
        result = await Runner.run(agent, system_context)
        
        agent_response = str(result.final_output)
        
        # Add agent response to session
        messages.append({
            "role": "agent",
            "content": agent_response
        })
        PolicyRepository.update_session_messages(session_id, messages)
        
        # Add delay to prevent rate limiting
        if DB_QUERY_DELAY > 0:
            await asyncio.sleep(DB_QUERY_DELAY)
        
        # Get updated policy data after agent run
        policy = PolicyRepository.get_policy(policy_id)
        client_data = PolicyRepository.get_client_data(policy_id)
        vehicle_data = PolicyRepository.get_vehicle_data(policy_id)
        quotations = PolicyRepository.get_quotations(policy_id)
        
        # Refresh session from DB to get latest messages
        session = PolicyRepository.get_session(session_id)
        
        return {
            "response": agent_response,
            "policy_state": policy.state,
            "intention_confirmed": policy.intention,
            "insurance_type": policy.insurance_type,
            "client_saved": client_data is not None,
            "client_name": client_data.name if client_data else None,
            "client_email": client_data.email if client_data else None,
            "client_phone": client_data.phone if client_data else None,
            "vehicle_saved": vehicle_data is not None,
            "vehicle_make": vehicle_data.make if vehicle_data else None,
            "vehicle_model": vehicle_data.model if vehicle_data else None,
            "quotations": quotations,
            "messages": session["messages"]
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/{session_id}")
def get_session(session_id: str):
    """Get session data"""
    session = PolicyRepository.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    policy = PolicyRepository.get_policy(session["policy_id"])
    
    return {
        "session_id": session_id,
        "policy_id": session["policy_id"],
        "policy_state": policy.state,
        "messages": session["messages"]
    }

# Database Admin Endpoints
@app.get("/api/admin/policies")
def get_all_policies():
    """Get all policies for admin view"""
    try:
        policies = PolicyRepository.get_all_policies()
        return {"policies": jsonable_encoder(policies)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/clients")
def get_all_clients():
    """Get all client data for admin view"""
    try:
        clients = PolicyRepository.get_all_client_data()
        return {"clients": jsonable_encoder(clients)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/transitions")
def get_all_transitions():
    """Get all state transitions for admin view"""
    try:
        transitions = PolicyRepository.get_all_state_transitions()
        return {"transitions": jsonable_encoder(transitions)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/vehicles")
def get_all_vehicles():
    """Get all vehicle data for admin view"""
    try:
        vehicles = PolicyRepository.get_all_vehicle_data()
        return {"vehicles": jsonable_encoder(vehicles)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/quotations")
def get_all_quotations():
    """Get all quotations for admin view"""
    try:
        quotations = PolicyRepository.get_all_quotations()
        return {"quotations": jsonable_encoder(quotations)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/{session_id}/quotations")
async def get_quotations(session_id: str):
    """Get quotations for a policy"""
    try:
        session = PolicyRepository.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        policy_id = session["policy_id"]
        quotations = PolicyRepository.get_quotations(policy_id)
        
        return {
            "quotations": quotations,
            "count": len(quotations)
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/sessions")
def get_all_sessions():
    """Get all sessions for admin view"""
    try:
        sessions_list = PolicyRepository.get_all_sessions()
        return {"sessions": jsonable_encoder(sessions_list)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin")
def serve_admin_ui():
    """Serve admin database UI"""
    return FileResponse("src/ui/admin.html")

@app.get("/")
def serve_ui():
    """Serve UI"""
    return FileResponse("src/ui/index.html")

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

