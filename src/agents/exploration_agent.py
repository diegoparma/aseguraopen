"""
Exploration Agent - Valida información y detecta anomalías
(Este es el próximo agente a implementar - TEMPLATE)
"""
from agents import Agent, function_tool, RunContextWrapper
from src.db.repository import PolicyRepository
from typing import Any
import json

@function_tool
async def validate_client_data(ctx: RunContextWrapper[Any], policy_id: str) -> str:
    """Validate client data for anomalies and completeness"""
    try:
        # Obtener datos del cliente
        client_data = PolicyRepository.get_client_data(policy_id)
        
        if not client_data:
            return "❌ No client data found for this policy"
        
        anomalies = []
        
        # Validaciones básicas
        if not client_data.name or len(client_data.name.strip()) < 3:
            anomalies.append("Name too short or empty")
        
        if not client_data.email or "@" not in client_data.email:
            anomalies.append("Invalid email format")
        
        if not client_data.phone or len(client_data.phone) < 10:
            anomalies.append("Invalid phone number")
        
        if anomalies:
            # Guardar datos de exploración con anomalías
            PolicyRepository.save_exploration_data(
                policy_id=policy_id,
                validation_status="suspicious",
                anomalies={"issues": anomalies}
            )
            return f"⚠️ Anomalías detectadas: {', '.join(anomalies)}"
        else:
            # Todo válido
            PolicyRepository.save_exploration_data(
                policy_id=policy_id,
                validation_status="validated",
                anomalies=None
            )
            return f"✅ Client data validated successfully"
    
    except Exception as e:
        return f"❌ Error validating: {str(e)}"

@function_tool
async def check_fraud_indicators(ctx: RunContextWrapper[Any], policy_id: str) -> str:
    """Check for potential fraud indicators"""
    try:
        client_data = PolicyRepository.get_client_data(policy_id)
        if not client_data:
            return "❌ No client data found"
        
        fraud_risk = []
        
        # Ejemplo: flagged patterns
        if "test" in client_data.email.lower():
            fraud_risk.append("Test email pattern detected")
        
        if "+" in client_data.phone:
            # Podría ser legítimo (formato internacional)
            pass
        
        if fraud_risk:
            return f"🚨 Potential fraud indicators: {', '.join(fraud_risk)}"
        else:
            return "✅ No fraud indicators detected"
    
    except Exception as e:
        return f"❌ Error checking fraud: {str(e)}"

class ExplorationAgent:
    """Agent that validates and explores client information"""
    
    @staticmethod
    def create_agent():
        """Create the ExplorationAgent"""
        return Agent(
            name="ExplorationAgent",
            instructions="""You are an insurance exploration agent. Your job is to:
1. Validate all client data received from intake
2. Check for anomalies and potential fraud indicators
3. Ask clarifying questions if needed
4. Determine if the client passes exploration or needs further review
5. Prepare handoff to quotation phase

Be thorough but fair. Look for genuine issues, not trivial problems.""",
            tools=[validate_client_data, check_fraud_indicators],
        )

# Ejemplo de cómo usarlo con handoff:
# 
# exploration_tool = ExplorationAgent.create_agent().as_tool(
#     tool_name="handoff_to_exploration",
#     tool_description="Validate and explore client data before quotation"
# )
#
# # Luego agregarlo al IntakeAgent:
# intake_agent = Agent(
#     name="IntakeAgent",
#     tools=[..., exploration_tool],  # Agregar aquí
# )
