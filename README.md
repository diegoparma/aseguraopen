# aseguraOpen - Insurance Agent Platform

Multi-agent AI system for insurance quotations and policy management using OpenAI Agents SDK with Turso database for persistent cloud storage.

## Features

- 🤖 **Multi-Agent System**: Specialized agents for intake, exploration, quotation, payment, and issuance
- 💾 **Cloud Database**: Turso (SQLite-compatible) for persistent session and policy storage
- 🌐 **REST API**: FastAPI-based endpoints for chat and admin operations
- 📝 **Session Management**: Persistent sessions with full conversation history
- 🔄 **State Management**: Complete policy lifecycle tracking

## Tech Stack

- **Backend**: FastAPI + Uvicorn
- **AI**: OpenAI Agents SDK
- **Database**: Turso (libSQL)
- **Deployment**: Vercel (serverless)

## Prerequisites

- Python 3.10+
- OpenAI API key
- Turso account and database URL + auth token

## Local Setup

### 1. Clone and install

```bash
git clone <repo-url>
cd aseguraOpen
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

Create `.env` file:

```env
OPENAI_API_KEY=sk-...
TURSO_DATABASE_URL=libsql://your-db-name.region.turso.io
TURSO_AUTH_TOKEN=eyJ0eXAi...
DB_QUERY_DELAY=0
```

### 3. Initialize database

```bash
python scripts/setup_turso.py
```

### 4. Run the server

```bash
python app.py
```

Server runs on `http://localhost:8000`

## API Endpoints

### Chat
- `POST /api/chat/start` - Start new chat session
- `POST /api/chat/{session_id}/message` - Send message
- `GET /api/chat/{session_id}` - Get session state
- `GET /api/chat/{session_id}/restore` - Restore session

### Admin
- `GET /api/admin/sessions` - List sessions
- `GET /api/health` - Health check

## Project Structure

```
aseguraOpen/
├── app.py                 # Main app
├── requirements.txt       # Dependencies
├── src/
│   ├── config.py
│   ├── models.py
│   ├── agents/           # Agent implementations
│   ├── db/              # Database layer
│   └── utils/           # Utilities
├── scripts/             # Migration scripts
└── ui/                  # Web interface
```

## Database Schema

- **policies** - Insurance policies
- **sessions** - Chat sessions
- **client_data** - Customer information
- **exploration_data** - Exploration phase data
- **vehicle_data** - Vehicle details
- **quotation_data** - Quotation information
- **state_transitions** - Audit log

## Deployment

### Vercel

1. Push to GitHub
2. Connect repo to Vercel
3. Set environment variables
4. Deploy

## Troubleshooting

### Port already in use
```bash
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### Database connection fails
- Verify `.env` credentials
- Run `python scripts/setup_turso.py` to init schema

## License

MIT License
