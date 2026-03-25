# Unbounded

Character interaction system with persistent memory. Users create AI characters with personalities, then interact with them through text. The system tracks conversation history and evolving relationships using mem0.

## Architecture

| Layer | Tech | Details |
|---|---|---|
| Backend | FastAPI (Python 3.11+) | Auth, character CRUD, interaction handling, image generation |
| Frontend | Next.js (Node 20+) | Character browsing, creation forms, chat interface |
| Database | PostgreSQL | Users, characters, game states (Alembic migrations) |
| LLM | Ollama (local) | Runs llama2 or similar for character dialogue |
| Memory | mem0 | Persistent memory storage and retrieval per character |
| Image gen | Replicate, Stability, BFL, FLUX | Character portrait generation (multiple provider fallbacks) |
| Deploy | Docker Compose | Orchestrates backend, frontend, and Postgres |

## External API Keys Required

DeepSeek, BFL, Replicate, Stability, OpenAI, mem0, Hume (emotion analysis). See `.env.template` for the full list.

## Setup

```bash
cp .env.template .env   # fill in API keys
ollama serve             # start local LLM
ollama pull llama2
docker compose up -d
```

Services start at:
- Frontend: `localhost:3001`
- Backend API: `localhost:8000`
- Swagger docs: `localhost:8000/docs`

## Development (without Docker)

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# Migrations
alembic upgrade head
```

## Tests

```bash
cd backend && pytest       # game states, interactions, memory service, state management
cd frontend && npm test
```

4 test files in backend covering game states, interactions, memory service, and state management.

## Status

Working prototype. Character creation, interaction, and memory persistence are functional. Image generation depends on having valid API keys for at least one provider. The emotion analysis integration (Hume) is partially wired.

## License

MIT
