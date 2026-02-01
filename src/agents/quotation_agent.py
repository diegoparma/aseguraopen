"""
Quotation Agent - Generates quotations based on vehicle data
Flujo: Pedir patente → Guardar datos → Generar cotizaciones → Mostrar opciones
"""
from agents import Agent, function_tool, RunContextWrapper
from src.db.repository import PolicyRepository
from src.db.session import get_session_storage
from typing import Any
import json

@function_tool
async def collect_vehicle_data(
    ctx: RunContextWrapper[Any],
    policy_id: str,
    plate: str,
    make: str,
    model: str,
    year: int,
    engine_number: str = None,
    chassis_number: str = None,
    engine_displacement: int = None
) -> str:
    """Collect and save vehicle data"""
    try:
        vehicle = PolicyRepository.save_vehicle_data(
            policy_id=policy_id,
            plate=plate,
            make=make,
            model=model,
            year=year,
            engine_number=engine_number,
            chassis_number=chassis_number,
            engine_displacement=engine_displacement
        )
        return f"✅ Datos del vehículo guardados: {make} {model} ({year}). Patente: {plate}"
    except Exception as e:
        return f"❌ Error al guardar datos del vehículo: {str(e)}"

@function_tool
async def generate_available_quotations(
    ctx: RunContextWrapper[Any],
    policy_id: str,
    insurance_type: str
) -> str:
    """Generate quotations for the vehicle"""
    try:
        quotations = PolicyRepository.generate_quotations(
            policy_id=policy_id,
            insurance_type=insurance_type
        )
        
        if not quotations:
            return f"❌ No se pudieron generar cotizaciones para tipo de seguro: {insurance_type}"
        
        # Format quotations for display
        quotes_text = f"✅ Generadas {len(quotations)} opciones de cotización:\n\n"
        for i, q in enumerate(quotations, 1):
            quotes_text += f"{i}. {q['coverage_type']} - {q['coverage_level']}\n"
            quotes_text += f"   Prima Mensual: ${q['monthly_premium']:.2f}\n"
            quotes_text += f"   Prima Anual: ${q['annual_premium']:.2f}\n"
            quotes_text += f"   Deductible: ${q['deductible']:.2f}\n\n"
        
        return quotes_text
    except Exception as e:
        return f"❌ Error al generar cotizaciones: {str(e)}"

@function_tool
async def get_policy_context(
    ctx: RunContextWrapper[Any],
    policy_id: str
) -> str:
    """Get current policy context"""
    try:
        policy = PolicyRepository.get_policy(policy_id)
        client_data = PolicyRepository.get_client_data(policy_id)
        vehicle_data = PolicyRepository.get_vehicle_data(policy_id)
        quotations = PolicyRepository.get_quotations(policy_id)
        
        context = f"""CONTEXTO ACTUAL:
- Estado: {policy.state}
- Tipo de Seguro: {policy.insurance_type or "No especificado"}
- Cliente: {client_data.name if client_data else "No completado"}
- Vehículo: {f"{vehicle_data.make} {vehicle_data.model}" if vehicle_data else "No ingresado"}
- Cotizaciones: {f"{len(quotations)} opciones disponibles" if quotations else "No generadas"}"""
        
        return context
    except Exception as e:
        return f"❌ Error al obtener contexto: {str(e)}"

@function_tool
async def move_to_quotation_state(
    ctx: RunContextWrapper[Any],
    policy_id: str
) -> str:
    """Move policy from loaded to quotation state"""
    try:
        policy = PolicyRepository.get_policy(policy_id)
        
        if policy.state != "loaded":
            return f"ℹ️ La póliza ya está en estado: {policy.state}"
        
        # Update state to quotation
        PolicyRepository.update_policy_state(
            policy_id=policy_id,
            new_state="quotation",
            reason="Iniciando fase de cotización",
            agent="QuotationAgent"
        )
        
        return f"✅ Póliza en fase de cotización. Ahora generaremos tus opciones."
    except Exception as e:
        return f"❌ Error al cambiar estado: {str(e)}"

@function_tool
async def select_quotation_and_move_to_payment(
    ctx: RunContextWrapper[Any],
    policy_id: str,
    quotation_index: int
) -> str:
    """Select a quotation and move to payment phase"""
    try:
        quotations = PolicyRepository.get_quotations(policy_id)
        
        if not quotations:
            return "❌ No hay cotizaciones disponibles"
        
        if quotation_index < 1 or quotation_index > len(quotations):
            return f"❌ Opción inválida. Elige entre 1 y {len(quotations)}"
        
        # Get selected quotation (0-indexed)
        selected = quotations[quotation_index - 1]
        
        # Update state to payment (no need to save selection separately)
        PolicyRepository.update_policy_state(
            policy_id=policy_id,
            new_state="payment",
            reason=f"Cotización seleccionada: {selected['coverage_type']} - {selected['coverage_level']}",
            agent="QuotationAgent"
        )
        
        return f"✅ Cotización {quotation_index} seleccionada: {selected['coverage_type']} - {selected['coverage_level']}\nPrima Mensual: ${selected['monthly_premium']:.2f}\nProcediendo al pago..."
    except Exception as e:
        return f"❌ Error al seleccionar cotización: {str(e)}"


class QuotationAgent:
    """Agent for generating vehicle quotations"""
    
    INSTRUCTIONS = """Eres un agente de seguros especializado en cotizaciones. Tu ÚNICO trabajo es obtener la PATENTE del vehículo y generar cotizaciones.

**MÁXIMA PRIORIDAD - ORDEN EXACTO:**
1. Si estado es "loaded", LLAMA INMEDIATAMENTE: move_to_quotation_state(policy_id)
2. El cliente VIENE del IntakeAgent (ya tiene nombre, email, teléfono)
3. TÚ SOLO necesitas: PATENTE (placa) del vehículo
4. NO pidas nombre, email, teléfono - ya están guardados

**FLUJO EXACTO:**

📍 PASO 0 - Cambiar estado (SOLO si está en "loaded"):
- LLAMA INMEDIATAMENTE: move_to_quotation_state(policy_id)
- El estado cambia a "quotation"

📍 PASO 1 - Saludo y presentación:
"Hola de nuevo, ahora vamos a configurar tu cotización de [AUTO/MOTO]. Para ello necesito la patente (placa) del vehículo."

📍 PASO 2 - Pedir SOLO la patente:
- Pregunta claramente: "¿Cuál es la patente (placa) del vehículo?"
- El cliente responde (ej: "ABC-1234")
- LLAMA INMEDIATAMENTE: collect_vehicle_data(policy_id, plate="ABC-1234")
- Responde: "✅ Guardé la patente. Generando cotizaciones..."

📍 PASO 3 - Generar cotizaciones:
- LLAMA: generate_available_quotations(policy_id, policy.insurance_type)
- Muestra las opciones ordenadas por precio
- Cada opción: Cobertura, Nivel, Prima Mensual, Prima Anual, Deductible

📍 PASO 4 - Responder preguntas (MIENTRAS el cliente decide):
- Detalles sobre cotizaciones
- Comparaciones
- Preguntas sobre cobertura
- NO presiones - deja decidir

📍 PASO 5 - Seleccionar cotización:
- El cliente dice "quiero la opción 1" o "prefiero la de $500"
- Identifica cuál quiere (1, 2, 3, etc.)
- Si no es claro, pregunta para confirmar
- LLAMA INMEDIATAMENTE: select_quotation_and_move_to_payment(policy_id, [número])
- Estado cambia a "payment" automáticamente

**REGLAS ABSOLUTAS:**
- NUNCA pidas nombre, email, teléfono (ya están guardados)
- NUNCA pidas marca o modelo (no es necesario)
- SOLO pide la PATENTE
- Respuestas cortas
- Usa contexto para verificar estado"""
    
    @staticmethod
    def create_agent() -> Agent:
        """Create a quotation agent"""
        return Agent(
            name="QuotationAgent",
            tools=[
                collect_vehicle_data,
                generate_available_quotations,
                get_policy_context,
                select_quotation_and_move_to_payment,
                move_to_quotation_state
            ],
            instructions=QuotationAgent.INSTRUCTIONS
        )

