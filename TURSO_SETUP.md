# 🚀 Configurar aseguraOpen con Turso

Este documento explica cómo configurar la aplicación para usar **Turso** como base de datos en la nube.

## ¿Por qué Turso?

- ✅ Usa **libSQL** (SQLite compatible 100%)
- ✅ Funciona perfectamente con **Vercel**
- ✅ Persistencia garantizada en la nube
- ✅ Sesiones almacenadas en BD (no en memoria)
- ✅ Plan gratuito generoso
- ✅ Replicación automática entre regiones

## Paso 1: Crear una Base de Datos en Turso

1. Ve a https://turso.tech
2. Crea una cuenta (gratis)
3. En el dashboard, crea una nueva base de datos:
   - Nombre: `aseguraopen` (o el que prefieras)
   - Región: Elige la más cercana a ti
4. Una vez creada, obtén:
   - **Database URL**: `libsql://your-db-name-xxx.turso.io`
   - **Auth Token**: `eyJhbGciOiJFZDI1NTE5In0...`

## Paso 2: Configurar Variables de Entorno

Edita `.env` y agrega tus credenciales:

```env
ENVIRONMENT=development
TURSO_DATABASE_URL=libsql://your-db-name-xxx.turso.io
TURSO_AUTH_TOKEN=eyJhbGciOiJFZDI1NTE5In0...
DB_QUERY_DELAY=0.1
```

**Nota:** `DB_QUERY_DELAY=0.1` agrega un pequeño delay (100ms) entre queries para evitar rate limiting de Turso.

## Paso 3: Crear el Schema en Turso

Ejecuta el script de setup:

```bash
python scripts/setup_turso.py
```

Deberías ver algo como:

```
🚀 Setting up Turso database...
   Database: libsql://your-db-name-xxx.turso.io
   [1/18] Executing... ✅
   [2/18] Executing... ✅
   ...
   [18/18] Executing... ✅

📊 Results:
   ✅ Successful: 18
   ⚠️  Errors/Warnings: 0

✅ Turso database schema initialized successfully!
```

## Paso 4: Instalar Dependencias

```bash
pip install -r requirements.txt
pip install httpx
```

## Paso 5: Ejecutar la Aplicación

```bash
python app.py
```

Ahora todas las sesiones y datos se guardarán en Turso automáticamente.

## Verificar que Funciona

Accede a:
- Chat: http://localhost:8000/
- Admin dashboard: http://localhost:8000/admin

Haz una conversación y verifica que:
1. Las sesiones se persisten ✅
2. Los datos se guardan en BD ✅
3. El admin dashboard muestra todo ✅

## Troubleshooting

### "Turso database configured - using HTTP API" pero la BD sigue vacía

**Necesitas ejecutar `python scripts/setup_turso.py` para crear el schema.**

Es el error exacto que experimentaste. Las tablas NO se crean automáticamente, necesitas ejecutar el script de migración.

### Error de autenticación

Verifica que `TURSO_AUTH_TOKEN` sea correcto. Cópialo exactamente del dashboard de Turso.

### Queries lentas

Aumenta `DB_QUERY_DELAY`:
- Para desarrollo: `0.1` (100ms)
- Para producción: `0` (sin delay)

### Error de conexión

Verifica que `TURSO_DATABASE_URL` sea correcto. Debe ser:
- ❌ Incorrecto: `your-database-name` (nombre sin URL)
- ✅ Correcto: `libsql://your-db-name-xxx.turso.io` (URL completa)

## Próximos Pasos

Cuando estés listo para production:

1. **Deploya a Vercel**: Frontend + API
2. **Usa Railway para el backend**: FastAPI + Uvicorn
3. **Turso sigue siendo tu BD**: Funciona igual en cloud

La configuración de Turso será la misma en production (solo necesitas las credenciales en las env vars de la plataforma).

## Comandos Útiles

```bash
# Crear/recrear el schema en Turso
python scripts/setup_turso.py

# Ejecutar tests con sesiones persistidas
python test_turso_sessions.py

# Ver estado del servidor
curl http://localhost:8000/health

# Ver estado de la BD
curl http://localhost:8000/api/admin/policies
```
     - `messages` (TEXT - JSON array)
     - `context_built` (INTEGER)
     - `created_at` (TIMESTAMP)
     - `updated_at` (TIMESTAMP)

## Running Locally (SQLite)

No configuration needed! The app automatically uses local SQLite:

```bash
# Initialize database with sessions table
python scripts/init_db.py

# Run the server
python app.py
```

The app will create/use `aseguraopen.db` locally.

## Setting Up for Turso

### 1. Create a Turso Account

Go to [turso.tech](https://turso.tech) and sign up for free.

### 2. Create a Database

```bash
# Install Turso CLI
brew install tursodatabase/tap/turso

# Login
turso auth login

# Create a new database
turso db create aseguraopen

# Get connection details
turso db show aseguraopen --http-address
```

### 3. Get Your Credentials

```bash
# Show database connection string
turso db show aseguraopen --http-address

# Create auth token
turso db tokens create aseguraopen
```

### 4. Configure Environment

Create a `.env` file in the project root (copy from `.env.example`):

```env
# Turso Database Configuration
TURSO_DATABASE_URL=libsql://your-db-name-xxx.turso.io
TURSO_AUTH_TOKEN=eyJhbGciOiJFZDI1NTE5In0...

# Optional: Add delay (in seconds) to prevent rate limiting
# Recommended: 0.1 for Turso (HTTP latency)
DB_QUERY_DELAY=0.1

ENVIRONMENT=production
```

### 5. Run Server with Turso

```bash
# Make sure .env is in project root
python app.py
```

The app will automatically:
- Detect Turso credentials from `.env`
- Connect via HTTP API instead of local SQLite
- Use the database for all queries

## Monitoring

### Local (SQLite)

```bash
# Check database directly
sqlite3 aseguraopen.db

# View sessions
sqlite3 aseguraopen.db "SELECT session_id, messages_count, created_at FROM sessions ORDER BY created_at DESC LIMIT 10;"
```

### Turso Dashboard

- Go to [console.turso.tech](https://console.turso.tech)
- Select your database
- Use the SQL Editor to query sessions
- View metrics and usage

### Admin Dashboard

While running, visit:
- **http://localhost:8000/admin** - Admin panel
- **/api/admin/sessions** - JSON list of all sessions

## Rate Limiting

If you experience timeouts with Turso:

1. Increase the delay in `.env`:
   ```env
   DB_QUERY_DELAY=0.5
   ```

2. Turso has generous free tier limits:
   - 9 GB storage
   - Unlimited queries
   - But HTTP latency is ~100-200ms

## Migration from SQLite to Turso

No migration needed! The app handles both automatically:

1. **Development (SQLite)**:
   - No `.env` file needed
   - Uses local `aseguraopen.db`
   - Sessions stored in DB immediately

2. **Production (Turso)**:
   - Add `.env` with Turso credentials
   - Same code, different backend
   - Scalable to production

## Testing

Run the included test suite:

```bash
# Test complete session flow
python test_turso_sessions.py

# Expected output: All tests passing ✅
```

This test verifies:
- Session creation
- Message persistence
- Session restoration
- Admin endpoints

## Next Steps for Production

1. **Add Turso credentials to your deployment platform**:
   - Vercel: Environment Variables
   - Railway: Variables
   - Render: Environment Variables

2. **Deploy backend to Railway or Render**:
   ```bash
   # Use vercel.json or railway.toml for configuration
   ```

3. **Deploy frontend to Vercel**:
   - Static HTML/JS can run on Vercel Functions
   - Or host separately (Netlify, GitHub Pages)

## Troubleshooting

### "no such table: sessions"

Make sure you ran the initialization:

```bash
python scripts/init_db.py
```

### "Turso connection failed"

Check your `.env`:
- `TURSO_DATABASE_URL` should be complete
- `TURSO_AUTH_TOKEN` should be valid
- Test with `curl` or Postman

### "Query timeout"

Increase the delay:

```env
DB_QUERY_DELAY=0.3
```

Or check Turso dashboard for rate limiting.

## Architecture

```
┌─────────────────┐
│   FastAPI App   │
│    (app.py)     │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Router  │
    └────┬────┘
         │
    ┌────▼──────────────┐
    │ PolicyRepository  │
    │ (business logic)  │
    └────┬──────────────┘
         │
    ┌────▼────────────────┐
    │ DatabaseConnection  │
    │ (adapter pattern)   │
    └────┬────────────────┘
         │
    ┌────┴────────────┐
    │                 │
┌───▼──────┐   ┌──────▼──┐
│  SQLite  │   │  Turso  │
│ (local)  │   │ (cloud) │
└──────────┘   └─────────┘
```

The adapter pattern allows seamless switching between SQLite and Turso without changing application code.
