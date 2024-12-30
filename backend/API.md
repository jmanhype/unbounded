# Unbounded API Documentation

## OpenAPI Specification

```yaml
openapi: 3.0.0
info:
  title: Unbounded API
  description: API for character interaction and memory management system
  version: 1.0.0

servers:
  - url: http://localhost:8000
    description: Development server

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    User:
      type: object
      properties:
        id:
          type: string
          format: uuid
        username:
          type: string
        email:
          type: string
          format: email
        created_at:
          type: string
          format: date-time

    Character:
      type: object
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
        age:
          type: integer
        personality:
          type: string
        background:
          type: string
        image_url:
          type: string
        created_at:
          type: string
          format: date-time

    Interaction:
      type: object
      properties:
        id:
          type: string
          format: uuid
        character_id:
          type: string
          format: uuid
        content:
          type: string
        response:
          type: object
        timestamp:
          type: string
          format: date-time

    GameState:
      type: object
      properties:
        id:
          type: string
          format: uuid
        character_id:
          type: string
          format: uuid
        health:
          type: integer
        energy:
          type: integer
        happiness:
          type: integer
        hunger:
          type: integer
        fatigue:
          type: integer
        stress:
          type: integer
        location:
          type: string
        activity:
          type: string
        timestamp:
          type: string
          format: date-time

paths:
  /auth/signup:
    post:
      summary: Create new user account
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                username:
                  type: string
                email:
                  type: string
                  format: email
                password:
                  type: string
      responses:
        '200':
          description: User created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'

  /auth/login:
    post:
      summary: Login to get access token
      requestBody:
        required: true
        content:
          application/x-www-form-urlencoded:
            schema:
              type: object
              properties:
                username:
                  type: string
                password:
                  type: string
      responses:
        '200':
          description: Login successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token:
                    type: string
                  token_type:
                    type: string

  /characters:
    get:
      summary: Get all characters
      security:
        - bearerAuth: []
      responses:
        '200':
          description: List of characters
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Character'

    post:
      summary: Create new character
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                age:
                  type: integer
                personality:
                  type: string
                background:
                  type: string
      responses:
        '200':
          description: Character created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Character'

  /characters/{character_id}:
    get:
      summary: Get character by ID
      security:
        - bearerAuth: []
      parameters:
        - name: character_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Character details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Character'

  /characters/{character_id}/interact:
    post:
      summary: Interact with character
      security:
        - bearerAuth: []
      parameters:
        - name: character_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                content:
                  type: string
      responses:
        '200':
          description: Interaction response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Interaction'

  /characters/{character_id}/state:
    get:
      summary: Get character state
      security:
        - bearerAuth: []
      parameters:
        - name: character_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Character state
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GameState'
```

## Authentication

All endpoints except `/auth/signup` and `/auth/login` require authentication using a JWT token.

To authenticate:
1. Create an account using `/auth/signup`
2. Login using `/auth/login` to get an access token
3. Include the token in the Authorization header: `Authorization: Bearer <token>`

## Rate Limiting

- Development: No rate limiting
- Production: 100 requests per minute per IP

## Error Responses

All error responses follow the format:
```json
{
  "detail": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "params": {}
  }
}
```

Common error codes:
- `INVALID_CREDENTIALS`: Username or password incorrect
- `USER_EXISTS`: Username already taken
- `CHARACTER_NOT_FOUND`: Character ID not found
- `VALIDATION_ERROR`: Invalid request data
- `UNAUTHORIZED`: Missing or invalid token
- `SERVER_ERROR`: Internal server error 