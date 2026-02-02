# Integración de Mercado Pago

Este documento explica cómo configurar y usar la integración de Mercado Pago para generar links de pago en AseguraOpen.

## 📋 Requisitos Previos

1. **Cuenta de Mercado Pago**: Necesitas una cuenta de vendedor en Mercado Pago
2. **Credenciales**: Access Token de tu cuenta de Mercado Pago

## 🔧 Configuración

### 1. Obtener Credenciales de Mercado Pago

1. Ingresa a [Mercado Pago Developers](https://www.mercadopago.com.ar/developers/panel/app)
2. Crea una aplicación o selecciona una existente
3. Ve a "Credenciales" en el menú lateral
4. Copia tu **Access Token** (Production o Test según el ambiente)

### 2. Configurar Variables de Entorno

Agrega las siguientes variables a tu archivo `.env`:

```env
# Mercado Pago Configuration
MERCADOPAGO_ACCESS_TOKEN=your-access-token-here
MERCADOPAGO_SUCCESS_URL=https://aseguraopen.onrender.com/payment/success
MERCADOPAGO_FAILURE_URL=https://aseguraopen.onrender.com/payment/failure
MERCADOPAGO_PENDING_URL=https://aseguraopen.onrender.com/payment/pending
MERCADOPAGO_WEBHOOK_URL=https://aseguraopen.onrender.com/webhooks/mercadopago
```

**Importante**: En Render, agrega estas variables en la configuración del servicio.

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

Esto instalará `mercadopago==2.2.3` junto con las demás dependencias.

## 🚀 Cómo Funciona

### Flujo de Pago

1. **El cliente llega al estado "payment"** después de seleccionar una cotización
2. **PaymentAgent genera automáticamente** un link de pago con Mercado Pago
3. **El cliente hace clic en el link** y es redirigido a Mercado Pago
4. **Completa el pago** usando:
   - Tarjeta de crédito/débito
   - Transferencia bancaria
   - Efectivo (Rapipago/Pago Fácil)
   - Saldo en Mercado Pago
5. **Una vez pagado**, el cliente confirma en el chat
6. **El agente procesa** y cambia el estado a "issued"

### Link de Pago Generado

El link incluye:
- **Producto**: Seguro AUTO/MOTO con tipo de cobertura
- **Descripción**: Nivel de cobertura y deducible
- **Monto**: Prima mensual de la cotización seleccionada
- **Datos del cliente**: Nombre, email, teléfono
- **Reference**: Policy ID para tracking
- **URLs de retorno**: Success, failure, pending
- **Webhook**: Para notificaciones automáticas

### Ejemplo de Uso

```python
# El agente automáticamente genera el link
payment_link = await generate_mercadopago_payment_link(policy_id)

# Respuesta al cliente:
"""
✅ ¡Link de pago generado exitosamente!

📋 DETALLES:
- Vehículo: Toyota Corolla 2020
- Cobertura: Terceros Completo - Premium
- Prima Mensual: $15000.00
- Deducible: $50000.00

💳 LINK DE PAGO:
https://www.mercadopago.com.ar/checkout/v1/redirect?pref_id=xxxxx

👆 Hace clic en el link para completar tu pago de forma segura con Mercado Pago.
"""
```

## 🔔 Webhooks (Opcional)

Para recibir notificaciones automáticas cuando se complete un pago, necesitas configurar un webhook endpoint.

### Endpoint de Webhook

El webhook está configurado para recibir notificaciones en:
```
POST /webhooks/mercadopago
```

### Implementación Recomendada

```python
@app.post("/webhooks/mercadopago")
async def mercadopago_webhook(request: Request):
    """Receive payment notifications from Mercado Pago"""
    try:
        body = await request.json()
        
        # Verificar tipo de notificación
        if body.get("type") == "payment":
            payment_id = body["data"]["id"]
            
            # Obtener detalles del pago
            # Actualizar estado de la póliza automáticamente
            
            return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

## 🧪 Testing

### Modo Sandbox (Test)

1. Crea [cuentas de prueba](https://www.mercadopago.com.ar/developers/es/docs/checkout-pro/additional-content/your-integrations/test/accounts)
2. Usa el **Access Token de Test** en tu `.env`
3. Usa las [tarjetas de prueba](https://www.mercadopago.com.ar/developers/es/docs/checkout-pro/integration-test/test-purchases) de Mercado Pago

### Tarjetas de Prueba

| Tarjeta          | Número           | CVV  | Fecha  | Resultado |
|------------------|------------------|------|--------|-----------|
| Mastercard       | 5031 7557 3453 0604 | 123  | 11/25  | Aprobado  |
| Visa             | 4509 9535 6623 3704 | 123  | 11/25  | Aprobado  |
| American Express | 3711 803032 57522   | 1234 | 11/25  | Aprobado  |

## 📊 Datos Guardados en la BD

Actualmente, el sistema genera el link pero no lo guarda en la BD. Para implementar persistencia:

### Agregar Tabla de Pagos

```sql
CREATE TABLE payments (
    id TEXT PRIMARY KEY,
    policy_id TEXT NOT NULL,
    preference_id TEXT NOT NULL,
    payment_link TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    amount REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP,
    FOREIGN KEY (policy_id) REFERENCES policies(id)
);
```

### Agregar Método al Repository

```python
@staticmethod
def save_payment_link(policy_id: str, payment_link: str, preference_id: str, amount: float):
    """Save payment link for a policy"""
    conn = DatabaseConnection.get_connection()
    payment_id = str(uuid.uuid4())
    
    conn.execute("""
        INSERT INTO payments (id, policy_id, preference_id, payment_link, amount)
        VALUES (?, ?, ?, ?, ?)
    """, [payment_id, policy_id, preference_id, payment_link, amount])
```

## 🔒 Seguridad

- **Nunca expongas** tu Access Token en el frontend
- **Valida siempre** las notificaciones de webhook usando la firma de Mercado Pago
- **Usa HTTPS** en todas las URLs
- **Almacena credenciales** en variables de entorno, nunca en código

## 📚 Recursos

- [Documentación Oficial Mercado Pago](https://www.mercadopago.com.ar/developers/es/docs/checkout-pro/overview)
- [SDK Python](https://github.com/mercadopago/sdk-python)
- [API Reference](https://www.mercadopago.com.ar/developers/es/reference)
- [Estado del Servicio](https://status.mercadopago.com/)

## 🐛 Troubleshooting

### Error: "Mercado Pago no está configurado"

**Solución**: Verifica que `MERCADOPAGO_ACCESS_TOKEN` esté configurado en tu `.env` o en Render.

### Error: "No hay cotización seleccionada"

**Solución**: Asegúrate de que el cliente haya seleccionado una cotización antes de llegar al paso de pago.

### El link no funciona

**Solución**: 
- Verifica que el Access Token sea válido
- Verifica que el monto sea mayor a 0
- Revisa los logs del servidor para ver el error específico

### Webhook no recibe notificaciones

**Solución**:
- Verifica que la URL del webhook sea accesible públicamente
- Confirma que la URL esté configurada correctamente en Mercado Pago
- Revisa los logs de Mercado Pago en el panel de desarrolladores

## 💡 Próximos Pasos

1. **Implementar persistencia** de payment links en la BD
2. **Agregar webhook endpoint** para notificaciones automáticas
3. **Crear endpoints** de success/failure/pending pages
4. **Agregar reconciliación** automática de pagos
5. **Implementar reembolsos** si es necesario

## 📞 Soporte

Para problemas con Mercado Pago:
- [Soporte Técnico Oficial](https://www.mercadopago.com/developers/es/support/center)
- [Discord de Desarrolladores](https://discord.com/invite/yth5bMKhdn)
