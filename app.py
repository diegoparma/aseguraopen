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

from src.db.repository import PolicyRepository
from src.db.connection import DatabaseConnection
from src.agents.intake_agent import IntakeAgent
from src.agents.quotation_agent import QuotationAgent
from src.agents.payment_agent import PaymentAgent
from src.agents.issuance_agent import IssuanceAgent
from agents import Runner

load_dotenv()

app = FastAPI(title="aseguraOpen - Insurance Agents")

# Initialize DB
DatabaseConnection.get_connection()

# Seed quotation templates on startup (if table exists)
try:
    PolicyRepository.seed_quotation_templates()
except Exception as e:
    # Table might not exist yet, will be created on first DB init
    pass

# Get DB query delay from env
DB_QUERY_DELAY = float(os.getenv("DB_QUERY_DELAY", "0"))

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
    uvicorn.run(app, host="0.0.0.0", port=8000)
