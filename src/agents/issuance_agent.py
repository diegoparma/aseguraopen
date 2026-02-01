"""
Issuance Agent - Handles policy issuance and delivery
Flujo: Generar póliza → Enviar a API → Cambiar estado a completado
"""
from agents import Agent, function_tool, RunContextWrapper
from src.db.repository import PolicyRepository
from typing import Any
import json

@function_tool
async def get_issuance_context(
    ctx: RunContextWrapper[Any],
    policy_id: str
) -> str:
    """Get current issuance context"""
    try:
        policy = PolicyRepository.get_policy(policy_id)
        client_data = PolicyRepository.get_client_data(policy_id)
        vehicle_data = PolicyRepository.get_vehicle_data(policy_id)
        quotations = PolicyRepository.get_quotations(policy_id)
        selected = None
        
        for q in quotations:
            if q.get('selected'):
                selected = q
                break
        
        vehicle_str = f"{vehicle_data.make} {vehicle_data.model} {vehicle_data.year}" if vehicle_data else "N/A"
        plate_str = vehicle_data.plate if vehicle_data else "N/A"
        coverage_str = f"{selected['coverage_type']} - {selected['coverage_level']}" if selected else "N/A"
        monthly_str = f"${selected['monthly_premium']:.2f}" if selected else "N/A"
        
        context = f"""CONTEXTO PARA EMISIÓN:
- ID Póliza: {policy_id}
- Cliente: {client_data.name if client_data else "N/A"}
- Email: {client_data.email if client_data else "N/A"}
- Teléfono: {client_data.phone if client_data else "N/A"}
- Vehículo: {vehicle_str}
- Patente: {plate_str}
- Cobertura: {coverage_str}
- Prima Mensual: {monthly_str}"""
        
        return context
    except Exception as e:
        return f"❌ Error al obtener contexto: {str(e)}"

@function_tool
async def issue_policy_to_api(
    ctx: RunContextWrapper[Any],
    policy_id: str
) -> str:
    """Issue policy and send to external API"""
    try:
        policy = PolicyRepository.get_policy(policy_id)
        client_data = PolicyRepository.get_client_data(policy_id)
        vehicle_data = PolicyRepository.get_vehicle_data(policy_id)
        quotations = PolicyRepository.get_quotations(policy_id)
        
        # Find selected quotation
        selected = None
        for q in quotations:
            if q.get('selected'):
                selected = q
                break
        
        if not selected and quotations:
            selected = quotations[0]
        
        if not selected:
            return "❌ No hay cotización seleccionada para emitir"
        
        # Build policy data for API
        policy_data = {
            "policy_id": policy_id,
            "client": {
                "name": client_data.name,
                "email": client_data.email,
                "phone": client_data.phone
            },
            "vehicle": {
                "make": vehicle_data.make,
                "model": vehicle_data.model,
                "year": vehicle_data.year,
                "plate": vehicle_data.plate,
                "engine_number": vehicle_data.engine_number,
                "chassis_number": vehicle_data.chassis_number
            },
            "insurance": {
                "type": policy.insurance_type,
                "coverage_type": selected['coverage_type'],
                "coverage_level": selected['coverage_level'],
                "monthly_premium": selected['monthly_premium'],
                "annual_premium": selected['annual_premium'],
                "deductible": selected['deductible']
            }
        }
        
        # TODO: In production, send to actual API
        # response = requests.post("https://api.issuer.com/policies", json=policy_data)
        # if response.status_code != 200:
        #     raise Exception(f"API Error: {response.text}")
        
        # For now, simulate successful API call
        print(f"📤 Enviando póliza a API: {json.dumps(policy_data, indent=2)}")
        
        # Update state to completed
        PolicyRepository.update_policy_state(
            policy_id=policy_id,
            new_state="completed",
            reason="Póliza emitida y enviada a cliente",
            agent="IssuanceAgent"
        )
        
        return f"""✅ ¡PÓLIZA EMITIDA CON ÉXITO!

📋 DETALLES:
- Número de Póliza: {policy_id[:8]}...
- Enviada a: {client_data.email}
- Cobertura: {selected['coverage_type']} - {selected['coverage_level']}
- Vehículo: {vehicle_data.make} {vehicle_data.model} ({vehicle_data.year})
- Prima Anual: ${selected['annual_premium']:.2f}

Revisa tu email para descargar los documentos."""
    except Exception as e:
        return f"❌ Error al emitir póliza: {str(e)}"


class IssuanceAgent:
    """Agent that handles policy issuance - NON-INTERACTIVE"""
    
    INSTRUCTIONS = """Eres un agente de emisión automático. Tu ÚNICO trabajo es:
1. Revisar que todo esté listo
2. Emitir la póliza
3. Enviar a la API
4. Marcar como completado

**IMPORTANTE: NO INTERACTÚAS CON EL CLIENTE**
- Este agente es completamente automático
- Solo llama a las herramientas
- No haces preguntas

**FLUJO AUTOMÁTICO:**

🔧 PASO 1 - Obtener contexto:
- LLAMA: get_issuance_context(policy_id)
- Verifica que todos los datos estén presentes

🔧 PASO 2 - Emitir póliza:
- LLAMA: issue_policy_to_api(policy_id)
- Envía todo a la API
- Marca como completado

**RESPUESTA FINAL:**
- Solo confirma que se emitió correctamente
- El cliente recibirá el documento por email""",
    
    @staticmethod
    def create_agent():
        """Create the IssuanceAgent"""
        return Agent(
            name="IssuanceAgent",
            instructions=IssuanceAgent.INSTRUCTIONS,
            tools=[
                get_issuance_context,
                issue_policy_to_api
            ],
        )
