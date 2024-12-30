# Unbounded Architecture

## System Overview

```mermaid
graph TB
    subgraph "Frontend (Next.js)"
        UI[User Interface]
        SC[State Management]
        API[API Client]
    end

    subgraph "Backend (FastAPI)"
        REST[REST API]
        Auth[Authentication]
        BL[Business Logic]
        subgraph "Services"
            CS[Character Service]
            MS[Memory Service]
            IS[Interaction Service]
            GS[Game State Service]
        end
    end

    subgraph "External Services"
        Ollama[Ollama LLM]
        OpenAI[OpenAI]
        DeepSeek[DeepSeek]
        Replicate[Replicate]
        Stability[Stability AI]
        Hume[Hume AI]
    end

    subgraph "Storage"
        PG[(PostgreSQL)]
        Mem0[Memory Store]
    end

    UI --> SC
    SC --> API
    API --> REST
    REST --> Auth
    Auth --> BL
    BL --> CS & MS & IS & GS
    CS --> PG
    MS --> Mem0
    IS --> Ollama & OpenAI & DeepSeek
    GS --> PG
    IS --> Stability & Replicate & Hume
```

## Component Details

### Frontend
- **User Interface**: React components and pages
- **State Management**: Zustand for global state
- **API Client**: Axios for API communication

### Backend
- **REST API**: FastAPI endpoints and routers
- **Authentication**: JWT-based auth with bearer tokens
- **Business Logic**: Core application logic
- **Services**:
  - Character Service: Character management
  - Memory Service: Memory persistence using mem0
  - Interaction Service: Character interactions and responses
  - Game State Service: Character state management

### External Services
- **Ollama**: Local LLM for character interactions
- **OpenAI**: Embeddings and backup LLM
- **DeepSeek**: Alternative LLM provider
- **Replicate**: Additional AI models
- **Stability AI**: Image generation
- **Hume AI**: Emotion analysis

### Storage
- **PostgreSQL**: Main database for users, characters, and states
- **Memory Store**: Specialized storage for character memories

## Data Flow

1. User interacts with UI
2. Frontend sends API request
3. Backend authenticates request
4. Business logic processes request
5. Services interact with storage and external services
6. Response flows back to UI

## Security Layers

```mermaid
graph LR
    subgraph "Security"
        C[CORS]
        R[Rate Limiting]
        A[Authentication]
        Z[Authorization]
        E[Encryption]
    end

    Request --> C
    C --> R
    R --> A
    A --> Z
    Z --> E
    E --> Backend
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Production Environment"
        LB[Load Balancer]
        subgraph "Application"
            F1[Frontend 1]
            F2[Frontend 2]
            B1[Backend 1]
            B2[Backend 2]
        end
        DB[(Database)]
        Cache[Redis Cache]
    end

    User --> LB
    LB --> F1 & F2
    F1 & F2 --> B1 & B2
    B1 & B2 --> DB
    B1 & B2 --> Cache
```

## Development Workflow

```mermaid
graph LR
    Dev[Development] --> Test[Testing]
    Test --> Build[Build]
    Build --> Deploy[Deployment]
    Deploy --> Monitor[Monitoring]
    Monitor --> Dev
``` 