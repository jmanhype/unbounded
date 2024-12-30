"""Module for generating character backstories using LLM."""
from typing import Optional, Dict, Any, Literal
import os
import logging
import traceback
import json
import httpx
from fastapi import HTTPException
from dotenv import load_dotenv
import openai
import tiktoken

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load and validate API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OLLAMA_API_BASE = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))  # 2 minute timeout

# Configure OpenAI if key is available
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
    logger.info("OpenAI API key configured")
else:
    logger.warning("OPENAI_API_KEY environment variable is not set")

class BackstoryGenerator:
    """Class for generating character backstories using LLM."""

    def __init__(
        self, 
        backend: Literal["openai", "ollama"] = "ollama",
        model: str = "llama2",
        api_key: Optional[str] = None,
        api_base: Optional[str] = None
    ):
        """Initialize the backstory generator.
        
        Args:
            backend: Which LLM backend to use ("openai" or "ollama").
            model: Model to use (e.g. "gpt-3.5-turbo" for OpenAI or "mistral" for Ollama).
            api_key: Optional API key for OpenAI. If not provided, uses environment variable.
            api_base: Optional API base URL for Ollama. If not provided, uses environment variable.
        """
        self.backend = backend
        self.model = model
        
        if backend == "openai":
            self.api_key = api_key or OPENAI_API_KEY
            if not self.api_key:
                logger.error("No OpenAI API key found")
                raise ValueError("OpenAI API key not found")
            openai.api_key = self.api_key
        else:  # ollama
            self.api_base = api_base or OLLAMA_API_BASE
            if not self.api_base:
                logger.error("No Ollama API base URL found")
                raise ValueError("Ollama API base URL not found")
            
        logger.info(f"Initialized BackstoryGenerator with {backend} backend using {model} model")

    async def generate_backstory(
        self,
        character_name: str,
        character_description: str,
        tone: str = "balanced",
        length: str = "medium",
        themes: Optional[list[str]] = None,
    ) -> Dict[str, Any]:
        """Generate a character backstory using LLM.
        
        Args:
            character_name: Name of the character.
            character_description: Basic description of the character.
            tone: Desired tone of the backstory (e.g., "dark", "light", "balanced").
            length: Desired length of the backstory ("short", "medium", "long").
            themes: Optional list of themes to incorporate.
            
        Returns:
            Dictionary containing the generated backstory and metadata.
            
        Raises:
            HTTPException: If backstory generation fails.
        """
        try:
            logger.info("Starting backstory generation for character: %s", character_name)
            
            # Construct the prompt
            prompt = self._construct_prompt(
                character_name,
                character_description,
                tone,
                length,
                themes
            )
            logger.debug("Generated prompt: %s", prompt)
            
            try:
                if self.backend == "openai":
                    # Generate backstory using OpenAI
                    response = await openai.ChatCompletion.acreate(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "You are a creative writing assistant specializing in character backstories. Your responses should be well-structured, engaging, and maintain internal consistency."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,  # Moderate creativity
                        max_tokens=self._get_max_tokens(length),
                        top_p=0.9,
                        frequency_penalty=0.3,  # Reduce repetition
                        presence_penalty=0.3    # Encourage diverse content
                    )
                    content = response.choices[0].message.content.strip()
                else:  # ollama
                    # Generate backstory using Ollama
                    request_data = {
                        "model": self.model,
                        "prompt": f"You are a creative writing assistant specializing in character backstories. Your responses should be well-structured, engaging, and maintain internal consistency.\n\n{prompt}",
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "num_predict": self._get_max_tokens(length)
                        }
                    }
                    logger.debug("Ollama request data: %s", json.dumps(request_data))
                    
                    async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
                        try:
                            response = await client.post(
                                f"{self.api_base}/api/generate",
                                json=request_data
                            )
                            logger.debug("Ollama response status: %d", response.status_code)
                            logger.debug("Ollama response headers: %s", response.headers)
                            
                            if response.status_code != 200:
                                error_text = response.text
                                logger.error("Ollama API error response: %s", error_text)
                                raise HTTPException(
                                    status_code=500,
                                    detail=f"Ollama API returned error: {error_text}"
                                )
                            
                            response_data = response.json()
                            logger.debug("Ollama response data: %s", json.dumps(response_data))
                            
                            if "response" not in response_data:
                                logger.error("No response field in Ollama API response")
                                raise ValueError("Invalid response format from Ollama API")
                            
                            content = response_data["response"].strip()
                            if not content:
                                logger.error("Empty response content from Ollama")
                                raise ValueError("Empty response from Ollama")
                            
                        except httpx.TimeoutException as e:
                            logger.error("Timeout during Ollama API request: %s", str(e))
                            raise HTTPException(
                                status_code=504,
                                detail="Request to Ollama API timed out. Please try again."
                            )
                        except httpx.RequestError as e:
                            logger.error("Failed to make request to Ollama API: %s", str(e))
                            raise HTTPException(
                                status_code=503,
                                detail=f"Failed to connect to Ollama API: {str(e)}"
                            )
                        except json.JSONDecodeError as e:
                            logger.error("Failed to parse Ollama API response: %s", str(e))
                            raise HTTPException(
                                status_code=500,
                                detail="Failed to parse response from Ollama API"
                            )
                
                word_count = len(content.split())
                logger.info("Successfully generated backstory with %d words", word_count)
                
                backstory = {
                    "content": content,
                    "tone": tone,
                    "themes": themes or [],
                    "word_count": word_count,
                    "model": self.model,
                    "backend": self.backend
                }
                
                return backstory
                
            except Exception as e:
                error_msg = f"{self.backend.title()} API error: {str(e)}"
                logger.error(error_msg)
                raise HTTPException(status_code=500, detail=error_msg)
            
        except Exception as e:
            error_msg = f"Failed to generate backstory: {str(e)}"
            logger.error("%s\n%s", error_msg, traceback.format_exc())
            raise HTTPException(status_code=500, detail=error_msg)

    def _construct_prompt(
        self,
        character_name: str,
        character_description: str,
        tone: str,
        length: str,
        themes: Optional[list[str]] = None
    ) -> str:
        """Construct the prompt for backstory generation.
        
        Args:
            character_name: Name of the character.
            character_description: Basic description of the character.
            tone: Desired tone of the backstory.
            length: Desired length of the backstory.
            themes: Optional list of themes to incorporate.
            
        Returns:
            Constructed prompt string.
        """
        # Base prompt template
        prompt = f"""Create a compelling backstory for a character with the following details:

Name: {character_name}
Description: {character_description}

The backstory should have a {tone} tone and be of {length} length.
"""
        
        # Add themes if provided
        if themes:
            prompt += f"\nIncorporate the following themes: {', '.join(themes)}"
            
        # Add specific instructions based on length
        length_guidelines = {
            "short": "Keep the backstory concise, focusing on key events (around 200-300 words).",
            "medium": "Provide a balanced backstory with moderate detail (around 500-700 words).",
            "long": "Create a detailed backstory with rich character development (around 1000-1200 words)."
        }
        prompt += f"\n\n{length_guidelines.get(length, length_guidelines['medium'])}"
        
        # Add general guidelines
        prompt += """

Include:
- Key life events that shaped the character
- Relationships and connections
- Motivations and goals
- Personal struggles and growth
- Cultural and environmental influences

The backstory should feel natural and believable, avoiding clichés while maintaining internal consistency.

Format the response as a well-structured narrative with clear paragraphs."""
        
        return prompt
        
    def _get_max_tokens(self, length: str) -> int:
        """Get the maximum number of tokens based on desired length and backend.
        
        Args:
            length: Desired length of the backstory ("short", "medium", "long").
            
        Returns:
            Maximum number of tokens to generate.
        """
        # Approximate token counts for different lengths
        # These numbers are estimates, assuming ~1.5 tokens per word
        if self.backend == "openai":
            token_limits = {
                "short": 500,    # ~300 words
                "medium": 1200,  # ~700 words
                "long": 2000     # ~1200 words
            }
        else:  # ollama
            # Ollama models typically have larger context windows
            token_limits = {
                "short": 750,    # ~450 words
                "medium": 1800,  # ~1050 words
                "long": 3000     # ~1800 words
            }
        return token_limits.get(length, token_limits["medium"]) 