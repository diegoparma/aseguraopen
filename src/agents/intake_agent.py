"""
Intake Agent - Recopila datos del cliente al iniciar una póliza
Flujo: Saludo → Detectar intención → Pedir datos → Validar → Guardar
"""
from agents import Agent, function_tool, RunContextWrapper
from src.db.repository import PolicyRepository
from src.db.session import get_session_storage
from typing import Any
import json

@function_tool
async def start_policy() -> str:
    """Start a new policy for intake"""
    try:
        policy = PolicyRepository.create_policy("intake")
        return f"✅ Póliza creada con ID: {policy.id[:8]}... Estado: {policy.state}"
    except Exception as e:
        return f"❌ Error al crear póliza: {str(e)}"

@function_tool
async def set_insurance_intention(
    ctx: RunContextWrapper[Any],
    policy_id: str,
    insurance_type: str
) -> str:
    """Mark that customer has expressed interest in a specific insurance type (auto/moto)"""
    try:
        if insurance_type not in ["auto", "moto"]:
            return f"❌ Tipo de seguro inválido. Usa 'auto' o 'moto'"
        
        policy = PolicyRepository.set_intention(policy_id, insurance_type)
        return f"✅ Intención registrada: Seguro de {insurance_type}. Proceederemos a recopilar tus datos."
    except Exception as e:
        return f"❌ Error al registrar intención: {str(e)}"

@function_tool
async def validate_and_save_client_data(
    ctx: RunContextWrapper[Any],
    policy_id: str,
    name: str,
    email: str,
    phone: str
) -> str:
    """Validate and save client data - only call AFTER intention is confirmed"""
    try:
        # First validate the data
        validation = PolicyRepository.validate_client_data(name, email, phone)
        
        if not validation["valid"]:
            error_list = "\n".join([f"  • {e}" for e in validation["errors"]])
            return f"❌ Datos inválidos:\n{error_list}\n\nPor favor, proporciona datos válidos."
        
        # Check if intention was already set
        policy = PolicyRepository.get_policy(policy_id)
        if not policy.intention:
            return "❌ Primero debes confirmar tu intención de compra antes de proporcionar datos."
        
        # Save the validated data
        client_data = PolicyRepository.save_client_data(
            policy_id=policy_id,
            name=validation["data"]["name"],
            email=validation["data"]["email"],
            phone=validation["data"]["phone"]
        )
        
        return f"✅ Datos guardados correctamente:\n  • Nombre: {client_data.name}\n  • Email: {client_data.email}\n  • Teléfono: {client_data.phone}\n\nPerfecto, estamos listos para proceder a la siguiente fase."
    except Exception as e:
        return f"❌ Error al guardar datos: {str(e)}"

@function_tool
async def save_client_field(
    ctx: RunContextWrapper[Any],
    policy_id: str,
    field_name: str,
    field_value: str
) -> str:
    """Save a single client data field (name, email, or phone) - called progressively"""
    try:
        if field_name not in ["name", "email", "phone"]:
            return f"❌ Campo inválido: {field_name}. Usa 'name', 'email' o 'phone'"
        
        # Check if intention was set
        policy = PolicyRepository.get_policy(policy_id)
        if not policy.intention:
            return "❌ Primero confirma tu intención de compra antes de guardar datos."
        
        # Validate the specific field
        if field_name == "name" and (not field_value or len(field_value.strip()) < 2):
            return f"❌ {field_name}: debe tener al menos 2 caracteres"
        
        if field_name == "email" and ("@" not in field_value or "." not in field_value):
            return f"❌ {field_name}: debe ser un email válido"
        
        if field_name == "phone" and len(field_value.replace(" ", "").replace("+", "").replace("-", "")) < 8:
            return f"❌ {field_name}: debe tener al menos 8 dígitos"
        
        # Save the field
        update_dict = {field_name: field_value.strip()}
        client_data = PolicyRepository.update_client_data_partial(policy_id, **update_dict)
        
        saved_fields = []
        if client_data.name:
            saved_fields.append(f"Nombre: {client_data.name}")
        if client_data.email:
            saved_fields.append(f"Email: {client_data.email}")
        if client_data.phone:
            saved_fields.append(f"Teléfono: {client_data.phone}")
        
        saved_text = "\n  • ".join(saved_fields)
        return f"✅ {field_name.capitalize()} guardado correctamente.\n\nDatos guardados hasta ahora:\n  • {saved_text}"
    except Exception as e:
        return f"❌ Error al guardar {field_name}: {str(e)}"

@function_tool
async def get_policy_context(ctx: RunContextWrapper[Any], policy_id: str) -> str:
    """Get current policy and client information"""
    try:
        policy = PolicyRepository.get_policy(policy_id)
        if not policy:
            return f"❌ Póliza {policy_id} no encontrada"
        
        client_data = PolicyRepository.get_client_data(policy_id)
        
        result = f"📋 Contexto de la Póliza:\n"
        result += f"  • ID: {policy.id[:8]}...\n"
        result += f"  • Estado: {policy.state}\n"
        result += f"  • Intención: {'✅ Sí' if policy.intention else '❌ No'}\n"
        
        if policy.insurance_type:
            result += f"  • Tipo: {policy.insurance_type}\n"
        
        if client_data:
            result += f"  • Cliente: {client_data.name}\n"
            result += f"  • Email: {client_data.email}\n"
            result += f"  • Teléfono: {client_data.phone}\n"
        else:
            result += f"  • Cliente: Sin datos aún\n"
        
        return result
    except Exception as e:
        return f"❌ Error al obtener contexto: {str(e)}"

@function_tool
async def complete_intake_and_move_to_loaded(
    ctx: RunContextWrapper[Any],
    policy_id: str
) -> str:
    """Mark intake as complete and move to loaded phase"""
    try:
        policy = PolicyRepository.get_policy(policy_id)
        client_data = PolicyRepository.get_client_data(policy_id)
        
        # Verify all requirements are met
        if not policy.intention:
            return "❌ No hay intención confirmada"
        
        if not client_data or not client_data.name or not client_data.email or not client_data.phone:
            return "❌ Faltan datos del cliente"
        
        # Update state to loaded
        PolicyRepository.update_policy_state(
            policy_id=policy_id,
            new_state="loaded",
            reason="Intake completo - datos del cliente cargados",
            agent="IntakeAgent"
        )
        
        return f"✅ Intake completado. Datos cargados correctamente."
    except Exception as e:
        return f"❌ Error al completar intake: {str(e)}"

@function_tool
async def get_policy_context(ctx: RunContextWrapper[Any], policy_id: str) -> str:
    """Get current policy and client information"""
    try:
        policy = PolicyRepository.get_policy(policy_id)
        if not policy:
            return f"❌ Póliza {policy_id} no encontrada"
        
        client_data = PolicyRepository.get_client_data(policy_id)
        
        result = f"📋 Contexto de la Póliza:\n"
        result += f"  • ID: {policy.id[:8]}...\n"
        result += f"  • Estado: {policy.state}\n"
        result += f"  • Intención: {'✅ Sí' if policy.intention else '❌ No'}\n"
        
        if policy.insurance_type:
            result += f"  • Tipo: {policy.insurance_type}\n"
        
        if client_data:
            result += f"  • Cliente: {client_data.name}\n"
            result += f"  • Email: {client_data.email}\n"
            result += f"  • Teléfono: {client_data.phone}\n"
        else:
            result += f"  • Cliente: Sin datos aún\n"
        
        return result
    except Exception as e:
        return f"❌ Error al obtener contexto: {str(e)}"

class IntakeAgent:
    """Agent that handles client intake with proper flow"""
    
    @staticmethod
    def create_agent():
        """Create the IntakeAgent"""
        return Agent(
            name="IntakeAgent",
            instructions="""Eres un agente de seguros profesional de aseguraOpen. Tu ÚNICO trabajo es el INTAKE (recopilación de TODOS los datos).

**MÁXIMA PRIORIDAD - NO TERMINES HASTA TENER TODOS LOS DATOS:**
1. Nombre ✅
2. Email ✅
3. Teléfono ✅

Si NO tienes los 3, NO puedes terminar. Punto.

**FLUJO EXACTO (sigue estrictamente este orden):**

📍 PASO 1 - Saludo (SOLO si historial vacío):
"Hola, bienvenido a aseguraOpen. Ofrecemos seguros de AUTOS y MOTOS. ¿Cuál te interesa?"

📍 PASO 2 - Intención (SI: Intención confirmada = NO):
- Espera que diga "auto" o "moto"
- APENAS diga uno de esos → llama set_insurance_intention(policy_id, "auto" o "moto")
- Responde: "Perfecto. Ahora necesito tus datos..."

📍 PASO 3 - Nombre (SI: Intención = SÍ):
- Pregunta: "¿Tu nombre?"
- El cliente responde
- LLAMA INMEDIATAMENTE: save_client_field(policy_id, "name", "[lo que dijo]")
- Responde: "✅ Guardé tu nombre. Ahora tu email..."

📍 PASO 4 - Email (DESPUÉS de guardar nombre):
- Pregunta: "¿Tu email?"
- El cliente responde
- LLAMA INMEDIATAMENTE: save_client_field(policy_id, "email", "[lo que dijo]")
- Responde: "✅ Email guardado. Ahora tu teléfono..."

📍 PASO 5 - Teléfono (DESPUÉS de guardar email):
- Pregunta: "¿Tu teléfono?"
- El cliente responde
- LLAMA INMEDIATAMENTE: save_client_field(policy_id, "phone", "[lo que dijo]")
- Responde: "✅ Perfecto, tengo todos tus datos. Pasamos a cotización."

**REGLAS INAMOVIBLES - LEER CON MUCHA ATENCIÓN:**
1. SIEMPRE LLAMA save_client_field cuando el cliente da un dato - SIN EXCEPCIONES
2. ESPERA a que save_client_field termine antes de pasar al siguiente dato
3. SI save_client_field devuelve error, repite el paso (pide el dato de nuevo)
4. NO SALTES PASOS - primero nombre, luego email, luego teléfono
5. DESPUÉS DE GUARDAR TELÉFONO, LLAMA INMEDIATAMENTE: complete_intake_and_move_to_loaded(policy_id)
6. NO TERMINES HASTA HABER LLAMADO complete_intake_and_move_to_loaded
7. Si el cliente dice otro dato antes de que pidas, guárdalo igual
8. Si ya guardaste 2 datos, INSISTE en el 3ro. No dejes a medias.

**RESPUESTAS CORTAS Y DIRECTAS:**
- Pregunta clara + guardado del dato + siguiente pregunta
- Máximo 2 frases por respuesta
- Usa ✅ para confirmaciones""",
            tools=[start_policy, set_insurance_intention, save_client_field, validate_and_save_client_data, get_policy_context, complete_intake_and_move_to_loaded],
        )
