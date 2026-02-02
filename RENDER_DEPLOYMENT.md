# Deployment en Render.com

Esta guía te ayudará a deployar aseguraOpen en Render.com

## Prerequisitos

- ✅ Cuenta en [Render.com](https://render.com)
- ✅ Repositorio GitHub conectado
- ✅ Variables de entorno de Turso y OpenAI

## Pasos para Deploy

### 1. Conectar GitHub a Render
1. Ve a [render.com](https://render.com)
2. Click en "New +" → "Web Service"
3. Conecta tu repositorio GitHub (diegoparma/aseguraopen)
4. Autoriza Render para acceder a tu GitHub

### 2. Configurar Web Service
- **Name**: aseguraopen
- **Runtime**: Python 3
- **Build Command**: (dejar vacío, usa render.yaml)
- **Start Command**: (dejar vacío, usa Procfile)

### 3. Agregar Variables de Entorno
En **Environment Variables**, agrega:

```
OPENAI_API_KEY=sk-proj-XXXXXXXXXXXX
TURSO_DATABASE_URL=libsql://aseguraopen-diegoparma.aws-us-east-1.turso.io
TURSO_AUTH_TOKEN=eyJhbGciOi...
ENVIRONMENT=production
DB_QUERY_DELAY=0.1
```

### 4. Deploy
1. Click en "Create Web Service"
2. Render automáticamente construirá e iniciará la app
3. Espera 2-5 minutos para el primer deploy

### 5. Verificar Deployment
Una vez que aparezca "Live", prueba:
```bash
curl https://aseguraopen.onrender.com/health
```

Deberías ver:
```json
{"status": "ok"}
```

## Usar la API Desplegada

La API está disponible en: `https://aseguraopen.onrender.com`

### Endpoint OpenAI Compatible
```bash
curl -X POST https://aseguraopen.onrender.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hola, quiero asegurar mi auto"}
    ],
    "model": "aseguraopen"
  }'
```

## Monitoreo

1. En el dashboard de Render, puedes ver:
   - **Logs**: en tiempo real
   - **Metrics**: CPU, memoria, etc.
   - **Events**: historial de deploys

## Troubleshooting

**Error: Build failed**
- Revisa los logs en Render
- Asegúrate que `requirements.txt` tenga todas las dependencias
- Verifica que el repositorio esté actualizado con `git push`

**Error: Module not found**
- Ejecuta `pip install -r requirements.txt` localmente
- Agrega la faltante a requirements.txt
- Push nuevamente

**Error: Environment variables not set**
- Recarga la página del dashboard
- Reinicia el service en Render

## URLs Útiles

- Dashboard Render: https://dashboard.render.com
- Logs en tiempo real: https://dashboard.render.com/web/{service-id}/logs
- Health Check: https://aseguraopen.onrender.com/health
- Chat Completions API: https://aseguraopen.onrender.com/v1/chat/completions

## Notas

- El primer deploy tarda 3-5 minutos
- Render sleep services inactivos después de 15 min (plan gratuito)
- El primer request después del sleep tarda ~30s (cold start)
- Usa plan pagado para evitar sleep ($7/mes aprox)
