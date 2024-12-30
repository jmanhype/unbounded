# Unbounded

A character interaction and memory management system that creates dynamic, personality-driven AI characters with persistent memory and evolving relationships.

## Features

- Character creation and management
- Dynamic personality system
- Memory persistence using mem0
- Image generation with multiple providers
- Local LLM integration with Ollama
- Real-time character state tracking
- Context-aware interactions
- User authentication and authorization

## Prerequisites

- Docker and Docker Compose
- Ollama running locally (for local LLM support)
- API keys for various services
- Python 3.11+ (for development)
- Node.js 20+ (for development)

## Project Structure

```
unbounded/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── models/         # Database models
│   │   ├── routers/        # API endpoints
│   │   ├── services/       # Business logic
│   │   └── utils/          # Helper functions
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Next.js pages
│   │   └── styles/         # CSS styles
│   ├── tests/              # Frontend tests
│   └── package.json        # Node.js dependencies
├── docker-compose.yml      # Docker configuration
├── .env.template           # Environment template
└── README.md              # Documentation
```

## Environment Setup

1. Copy `.env.template` to `.env`:
   ```bash
   cp .env.template .env
   ```

2. Fill in your API keys and configuration in `.env`:

   Required API Keys:
   - `DEEPSEEK_API_KEY`: For DeepSeek API access
   - `BFL_API_KEY`: For BFL API access
   - `REPLICATE_API_KEY`: For Replicate API access
   - `STABILITY_API_KEY`: For Stability API access
   - `OPENAI_API_KEY`: For OpenAI API access
   - `MEM0_API_KEY`: For memory management
   - `HUME_API_KEY` and `HUME_SECRET_KEY`: For emotion analysis

   Security Keys (generate secure values):
   ```bash
   # Generate secure keys using Python
   python -c 'import secrets; print(secrets.token_hex(32))'
   ```
   - `SECRET_KEY`: Main application secret key
   - `JWT_SECRET_KEY`: JWT token signing key

   Database Configuration:
   - `POSTGRES_USER`: Database username
   - `POSTGRES_PASSWORD`: Database password
   - `POSTGRES_DB`: Database name (default: unbounded_db)

## Running the Application

1. Start Ollama locally (required for LLM functionality):
   ```bash
   ollama serve
   ```

2. Pull required Ollama models:
   ```bash
   ollama pull llama2
   ```

3. Start the application services:
   ```bash
   docker compose up -d
   ```

4. The services will be available at:
   - Frontend: http://localhost:3001
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Development

1. Backend Development:
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   
   # Install dependencies
   cd backend
   pip install -r requirements.txt
   
   # Run tests
   pytest
   
   # Start development server
   uvicorn app.main:app --reload
   ```

2. Frontend Development:
   ```bash
   # Install dependencies
   cd frontend
   npm install
   
   # Run tests
   npm test
   
   # Start development server
   npm run dev
   ```

3. Database Migrations:
   ```bash
   # Generate migration
   alembic revision --autogenerate -m "description"
   
   # Apply migrations
   alembic upgrade head
   ```

## Testing

1. Backend Tests:
   ```bash
   cd backend
   pytest                 # Run all tests
   pytest -v             # Verbose output
   pytest -k "test_name" # Run specific test
   pytest --cov         # Run with coverage
   ```

2. Frontend Tests:
   ```bash
   cd frontend
   npm test             # Run all tests
   npm test -- --watch  # Watch mode
   npm run test:coverage # Run with coverage
   ```

## API Documentation

Detailed API documentation is available in multiple formats:

1. OpenAPI/Swagger UI: http://localhost:8000/docs
2. ReDoc: http://localhost:8000/redoc
3. Markdown: [API.md](backend/API.md)

## Error Handling

1. HTTP Status Codes:
   - 200: Success
   - 400: Bad Request
   - 401: Unauthorized
   - 403: Forbidden
   - 404: Not Found
   - 422: Validation Error
   - 500: Internal Server Error

2. Error Response Format:
   ```json
   {
     "detail": {
       "code": "ERROR_CODE",
       "message": "Human readable message",
       "params": {}
     }
   }
   ```

## Deployment

1. Development:
   - Uses local Ollama for LLM
   - SQLite database
   - Debug logging
   - CORS allows all origins

2. Production:
   - Configure external LLM service
   - PostgreSQL database
   - Structured logging to file
   - CORS restricted to allowed origins
   - Rate limiting enabled
   - SSL/TLS required

## Security Notes

- Never commit the `.env` file to version control
- Keep your API keys and secrets secure
- Regularly rotate your security keys
- Use strong, unique values for `SECRET_KEY` and `JWT_SECRET_KEY`
- Monitor your API key usage for any unauthorized access
- Enable rate limiting in production
- Use HTTPS in production
- Implement proper CORS policies
- Regular security audits
- Keep dependencies updated

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

### Development Guidelines

1. Code Style:
   - Backend: Follow PEP 8 and use Ruff for linting
   - Frontend: Follow ESLint and Prettier configurations
   - Use meaningful variable and function names
   - Add type hints to all Python functions
   - Use TypeScript for frontend development

2. Testing:
   - Write tests for new features
   - Maintain test coverage above 80%
   - Use pytest fixtures and parametrize
   - Mock external services in tests

3. Documentation:
   - Update API documentation
   - Add docstrings to functions
   - Update README when needed
   - Document configuration changes

## License

[MIT License](LICENSE) 