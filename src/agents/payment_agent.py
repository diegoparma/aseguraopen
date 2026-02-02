"""
Payment Agent - Handles payment processing and methods
Flujo: Ofrecer métodos → Procesar pago → Confirmar → Pasar a emisión
"""
from agents import Agent, function_tool, RunContextWrapper
from src.db.repository import PolicyRepository
from typing import Any
import os
import mercadopago

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

@function_tool
async def generate_mercadopago_payment_link(
    ctx: RunContextWrapper[Any],
    policy_id: str
) -> str:
    """Generate a Mercado Pago payment link for the selected quotation"""
    try:
        # Get access token from environment
        access_token = os.getenv("MERCADOPAGO_ACCESS_TOKEN")
        if not access_token:
            return "❌ Error: Mercado Pago no está configurado. Contacta al administrador."
        
        # Get policy and quotation data
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
            return "❌ No hay cotización seleccionada para generar el link de pago"
        
        # Initialize Mercado Pago SDK
        sdk = mercadopago.SDK(access_token)
        
        # Create preference data
        preference_data = {
            "items": [
                {
                    "title": f"Seguro {policy.insurance_type.upper()} - {selected['coverage_type']}",
                    "description": f"Cobertura {selected['coverage_level']} - Deducible ${selected['deductible']:.2f}",
                    "quantity": 1,
                    "unit_price": float(selected['monthly_premium']),
                    "currency_id": "ARS"
                }
            ],
            "payer": {
                "name": client_data.name if client_data else "Cliente",
                "email": client_data.email if client_data else "cliente@example.com",
                "phone": {
                    "number": client_data.phone if client_data else ""
                }
            },
            "back_urls": {
                "success": os.getenv("MERCADOPAGO_SUCCESS_URL", "https://aseguraopen.onrender.com/payment/success"),
                "failure": os.getenv("MERCADOPAGO_FAILURE_URL", "https://aseguraopen.onrender.com/payment/failure"),
                "pending": os.getenv("MERCADOPAGO_PENDING_URL", "https://aseguraopen.onrender.com/payment/pending")
            },
            "auto_return": "approved",
            "external_reference": policy_id,
            "statement_descriptor": "AseguraOpen",
            "notification_url": os.getenv("MERCADOPAGO_WEBHOOK_URL", "https://aseguraopen.onrender.com/webhooks/mercadopago")
        }
        
        # Create preference
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]
        
        if preference_response["status"] != 201:
            return f"❌ Error al generar link de pago: {preference_response.get('response', {}).get('message', 'Error desconocido')}"
        
        # Get init_point (payment link)
        payment_link = preference.get("init_point")
        preference_id = preference.get("id")
        
        if not payment_link:
            return "❌ Error: No se pudo obtener el link de pago"
        
        # Save payment to database
        PolicyRepository.create_payment(
            policy_id=policy_id,
            quotation_id=selected['id'],
            amount=float(selected['monthly_premium']),
            preference_id=preference_id,
            payment_link=payment_link
        )
        
        vehicle_info = f"{vehicle_data.make} {vehicle_data.model} {vehicle_data.year}" if vehicle_data else "Vehículo"
        
        return f"""✅ ¡Link de pago generado exitosamente!

📋 DETALLES:
- Vehículo: {vehicle_info}
- Cobertura: {selected['coverage_type']} - {selected['coverage_level']}
- Prima Mensual: ${selected['monthly_premium']:.2f}
- Deducible: ${selected['deductible']:.2f}

💳 LINK DE PAGO:
{payment_link}

👆 Hace clic en el link para completar tu pago de forma segura con Mercado Pago.

Una vez que completes el pago, tu póliza se emitirá automáticamente."""
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"❌ Error al generar link de Mercado Pago: {str(e)}"


class PaymentAgent:
    """Agent that handles payment processing"""
    
    INSTRUCTIONS = """Eres un agente de pagos especializado. Tu trabajo es:
1. Ofrecer generar un link de pago con Mercado Pago
2. Generar el link de pago
3. Compartir el link con el cliente
4. ESPERAR a que confirme el pago
5. Procesar y cambiar a emisión

**FLUJO EXACTO:**

📍 PASO 1 - Saludo:
"Perfecto, llegó el momento de procesar tu pago. Voy a generar un link de pago seguro con Mercado Pago para que puedas completar tu compra."

📍 PASO 2 - Generar Link de Mercado Pago:
- LLAMA INMEDIATAMENTE: generate_mercadopago_payment_link(policy_id)
- El sistema generará un link único de pago
- Muestra el link al cliente de forma clara
- Explica que puede pagar con:
  * Tarjeta de crédito/débito
  * Transferencia bancaria
  * Efectivo (Rapipago/Pago Fácil)
  * Mercado Pago

📍 PASO 3 - ESPERAR CONFIRMACIÓN:
- El cliente hace clic en el link y paga
- ESPERA a que el cliente responda
- El cliente debe decir: "ya pagué", "listo", "pagado", "completé el pago", etc.
- CUANDO confirme que ya pagó, LLAMA INMEDIATAMENTE: process_payment(policy_id, "4") [4 = Mercado Pago]

📍 PASO 4 - Confirmación final:
- El estado cambia a "issued" automáticamente
- Confirma que todo está listo
- La póliza se emitirá en breve

**REGLAS INAMOVIBLES:**
- Genera SIEMPRE el link de Mercado Pago primero
- NO muestres los otros métodos de pago a menos que el cliente lo pida específicamente
- ESPERA a que confirme que YA PAGÓ antes de procesar
- Si dice "no pagué" o "después", ofrece esperar
- Respuestas amables y profesionales
- Una vez que confirma pago, procesa INMEDIATAMENTE
- El link de pago es único por póliza

**CÓMO DETECTAR CONFIRMACIÓN:**
- "ya pagué"
- "listo"
- "pagado"
- "confirmado"
- "hecho"
- "ok"
- "completé el pago"
- "terminé"
- Cualquier variante similar

**SI EL CLIENTE PREGUNTA POR OTROS MÉTODOS:**
- Ofrece mostrar los métodos tradicionales con show_payment_methods(policy_id)
- Pero recomienda Mercado Pago por ser más rápido y seguro"""
    
    @staticmethod
    def create_agent():
        """Create the PaymentAgent"""
        return Agent(
            name="PaymentAgent",
            instructions=PaymentAgent.INSTRUCTIONS,
            tools=[
                get_payment_context,
                generate_mercadopago_payment_link,
                show_payment_methods,
                process_payment
            ],
        )
