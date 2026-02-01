"""
Payment Agent - Handles payment processing and methods
Flujo: Ofrecer métodos → Procesar pago → Confirmar → Pasar a emisión
"""
from agents import Agent, function_tool, RunContextWrapper
from src.db.repository import PolicyRepository
from typing import Any

# Available payment methods
PAYMENT_METHODS = {
    "1": {"name": "Transferencia Bancaria", "description": "Transferencia a nuestra cuenta", "processing_days": 2},
    "2": {"name": "Tarjeta de Crédito", "description": "Visa, Mastercard, American Express", "processing_days": 0},
    "3": {"name": "Tarjeta de Débito", "description": "Débito inmediato desde tu cuenta", "processing_days": 0},
    "4": {"name": "Billetera Digital", "description": "PayPal, Mercado Pago, etc.", "processing_days": 0},
}

@function_tool
async def get_payment_context(
    ctx: RunContextWrapper[Any],
    policy_id: str
) -> str:
    """Get current payment context"""
    try:
        policy = PolicyRepository.get_policy(policy_id)
        client_data = PolicyRepository.get_client_data(policy_id)
        quotations = PolicyRepository.get_quotations(policy_id)
        selected = None
        
        # Find selected quotation
        for q in quotations:
            if q.get('selected'):
                selected = q
                break
        
        if not selected and quotations:
            selected = quotations[0]
        
        monthly = f"${selected['monthly_premium']:.2f}" if selected else "N/A"
        annual = f"${selected['annual_premium']:.2f}" if selected else "N/A"
        coverage = f"{selected['coverage_type']} - {selected['coverage_level']}" if selected else "No seleccionada"
        
        context = f"""CONTEXTO ACTUAL:
- Estado: {policy.state}
- Cliente: {client_data.name if client_data else "No especificado"}
- Cotización Seleccionada: {coverage}
- Prima Mensual: {monthly}
- Prima Anual: {annual}"""
        
        return context
    except Exception as e:
        return f"❌ Error al obtener contexto: {str(e)}"

@function_tool
async def process_payment(
    ctx: RunContextWrapper[Any],
    policy_id: str,
    payment_method: str
) -> str:
    """Process payment when client confirms"""
    try:
        if payment_method not in PAYMENT_METHODS:
            methods_text = "\n".join([f"{k}. {v['name']}" for k, v in PAYMENT_METHODS.items()])
            return f"❌ Método de pago inválido. Opciones disponibles:\n{methods_text}"
        
        method = PAYMENT_METHODS[payment_method]
        
        quotations = PolicyRepository.get_quotations(policy_id)
        selected = None
        for q in quotations:
            if q.get('selected'):
                selected = q
                break
        
        if not selected and quotations:
            selected = quotations[0]
        
        if not selected:
            return "❌ No hay cotización seleccionada para procesar el pago"
        
        client_data = PolicyRepository.get_client_data(policy_id)
        
        # Update policy state to issued (payment processed successfully)
        PolicyRepository.update_policy_state(
            policy_id=policy_id,
            new_state="issued",
            reason=f"Pago confirmado mediante {method['name']}",
            agent="PaymentAgent"
        )
        
        return f"""✅ ¡Pago procesado exitosamente!

📋 DETALLES DEL PAGO:
- Método: {method['name']}
- Monto: ${selected['monthly_premium']:.2f} (pago inicial)
- Cobertura: {selected['coverage_type']} - {selected['coverage_level']}
- Deductible: ${selected['deductible']:.2f}

Tu póliza se está emitiendo y se te enviará en breve."""
    except Exception as e:
        return f"❌ Error al procesar pago: {str(e)}"

@function_tool
async def show_payment_methods(
    ctx: RunContextWrapper[Any],
    policy_id: str
) -> str:
    """Show available payment methods"""
    try:
        methods_text = "💳 MÉTODOS DE PAGO DISPONIBLES:\n\n"
        for key, method in PAYMENT_METHODS.items():
            methods_text += f"{key}. {method['name']}\n"
            methods_text += f"   {method['description']}\n"
            methods_text += f"   Procesamiento: {'Inmediato' if method['processing_days'] == 0 else f'{method['processing_days']} días'}\n\n"
        
        return methods_text
    except Exception as e:
        return f"❌ Error al mostrar métodos de pago: {str(e)}"


class PaymentAgent:
    """Agent that handles payment processing"""
    
    INSTRUCTIONS = """Eres un agente de pagos especializado. Tu trabajo es:
1. Mostrar métodos de pago disponibles
2. Dejar que el cliente elija
3. ESPERAR a que confirme "ya lo pagué" o similar
4. Procesar el pago y cambiar a emisión

**FLUJO EXACTO:**

📍 PASO 1 - Saludo:
"Perfecto, llegó el momento de procesar tu pago. Te muestro nuestros métodos disponibles:"

📍 PASO 2 - Mostrar métodos:
- LLAMA: show_payment_methods(policy_id)
- Muestra todas las opciones disponibles
- Dile cuál te recomiendas (ej: tarjeta de crédito es más rápido)

📍 PASO 3 - El cliente elige un método:
- El cliente dice: "quiero pagar con tarjeta" o "opción 2"
- Identifica el número (1, 2, 3 o 4)
- Si no es claro, pregunta para confirmar

📍 PASO 4 - ESPERAR CONFIRMACIÓN:
- Dile instrucciones sobre cómo pagar (depende del método)
- ESPERA a que el cliente responda
- El cliente debe decir: "ya lo pagué", "listo", "pagado", etc.
- CUANDO confirme que ya pagó, LLAMA INMEDIATAMENTE: process_payment(policy_id, "[número método]")

📍 PASO 5 - Confirmación final:
- El estado cambia a "issued" automáticamente
- Confirma que todo está listo
- La póliza se emitirá en breve

**REGLAS INAMOVIBLES:**
- Muestra siempre los métodos disponibles primero
- NO presiones al cliente - deja que elija
- ESPERA a que confirme que YA PAGÓ antes de procesar
- Si dice "no pagué" o "después", ofrece esperar o cambiar método
- Respuestas amables y profesionales
- Una vez que confirma pago, procesa INMEDIATAMENTE
- El pago no es reversible desde aquí (es solo confirmación)

**CÓMO DETECTAR CONFIRMACIÓN:**
- "ya pagué"
- "listo"
- "pagado"
- "confirmado"
- "hecho"
- "ok"
- Cualquier variante similar"""
    
    @staticmethod
    def create_agent():
        """Create the PaymentAgent"""
        return Agent(
            name="PaymentAgent",
            instructions=PaymentAgent.INSTRUCTIONS,
            tools=[
                get_payment_context,
                show_payment_methods,
                process_payment
            ],
        )
