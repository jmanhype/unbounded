"""Image generation module using FLUX API."""
from typing import Optional, Dict, Any
import os
import httpx
import asyncio
import logging
import traceback
import base64
from fastapi import HTTPException

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

# Load and validate API key
BFL_API_KEY = os.environ.get("BFL_API_KEY")
if not BFL_API_KEY:
    logger.error("BFL_API_KEY environment variable is not set")
    raise ValueError("BFL_API_KEY environment variable is not set")
else:
    logger.info("BFL_API_KEY is set: %s", BFL_API_KEY)

class ImageGenerator:
    """Class for handling image generation using FLUX API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the image generator.
        
        Args:
            api_key: Optional API key for FLUX. If not provided, uses environment variable.
        """
        self.api_key = api_key or BFL_API_KEY
        if not self.api_key:
            logger.error("No FLUX API key found")
            raise ValueError("FLUX API key not found")
        
        logger.info("Initialized ImageGenerator with API key: %s", self.api_key)
        
        self.base_url = "https://api.bfl.ml"
        self.headers = {
            "X-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def get_task_result(self, task_id: str, silent: bool = False) -> Optional[dict]:
        """Poll for task result."""
        max_attempts = 30
        attempt = 0
        
        logger.info("Polling for task result: %s", task_id)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            while attempt < max_attempts:
                logger.debug("Polling attempt %d/%d", attempt + 1, max_attempts)
                
                try:
                    response = await client.get(
                        f"{self.base_url}/v1/get_result",
                        params={'id': task_id},
                        headers=self.headers
                    )
                    logger.debug("Poll response status: %d", response.status_code)
                    logger.debug("Poll response body: %s", response.text)
                    
                    if response.status_code != 200:
                        error_msg = f"Failed to get task status: {response.text}"
                        logger.error(error_msg)
                        raise HTTPException(status_code=response.status_code, detail=error_msg)
                    
                    result = response.json()
                    logger.debug("Poll result: %s", result)
                    
                    if result['status'] == 'Ready':
                        logger.info("Task completed successfully")
                        return result
                    elif result['status'] == 'failed':
                        error_msg = f"Task failed: {result.get('error', 'Unknown error')}"
                        logger.error(error_msg)
                        raise HTTPException(status_code=500, detail=error_msg)
                    
                except Exception as e:
                    error_msg = f"Error polling task status: {str(e)}\n{traceback.format_exc()}"
                    logger.error(error_msg)
                    raise HTTPException(status_code=500, detail=error_msg)
                
                attempt += 1
                await asyncio.sleep(2)
        
        error_msg = "Timeout waiting for task completion"
        logger.error(error_msg)
        raise HTTPException(status_code=504, detail=error_msg)

    async def generate_character_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        num_inference_steps: int = 50,
        guidance_scale: float = 7.5,
    ) -> str:
        """Generate a character image using FLUX API."""
        try:
            logger.info("Starting image generation with prompt: %s", prompt)
            
            # Prepare the payload
            payload = {
                "prompt": prompt,
                "width": width,
                "height": height,
                "model": "flux.1.1-pro",  # Using the pro model for best quality
                "steps": num_inference_steps,
                "guidance": guidance_scale
            }
            
            if negative_prompt:
                payload["negative_prompt"] = negative_prompt
            
            logger.debug("Request payload: %s", payload)
            logger.debug("Using headers: %s", self.headers)
            
            # Send the generation request
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    logger.debug("Sending POST request to %s", f"{self.base_url}/v1/flux-pro-1.1")
                    response = await client.post(
                        f"{self.base_url}/v1/flux-pro-1.1",
                        headers=self.headers,
                        json=payload
                    )
                    logger.debug("Response status: %d", response.status_code)
                    logger.debug("Response body: %s", response.text)
                    
                    if response.status_code != 200:
                        error_msg = f"Failed to start generation task: {response.text}"
                        logger.error(error_msg)
                        raise HTTPException(status_code=response.status_code, detail=error_msg)
                    
                    result = response.json()
                    logger.debug("Response JSON: %s", result)
                    
                    task_id = result.get('id')
                    if not task_id:
                        error_msg = "No task ID in response"
                        logger.error(error_msg)
                        raise HTTPException(status_code=500, detail=error_msg)
                    
                    logger.info("Task started with ID: %s", task_id)
                    
                    # Poll for the result
                    result = await self.get_task_result(task_id)
                    if result and result.get('result', {}).get('sample'):
                        image_url = result['result']['sample']
                        logger.info("Image URL from FLUX API: %s", image_url)
                        return image_url
                    
                    error_msg = "Failed to get image URL from result"
                    logger.error(error_msg)
                    raise HTTPException(status_code=500, detail=error_msg)
                    
                except httpx.RequestError as e:
                    error_msg = f"Request failed: {str(e)}\n{traceback.format_exc()}"
                    logger.error(error_msg)
                    raise HTTPException(status_code=500, detail=error_msg)
                
        except Exception as e:
            error_msg = f"Image generation failed: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

    async def save_image_locally(self, image_url: str, character_id: str) -> str:
        """Download and save an image locally.
        
        Args:
            image_url: URL of the image to download.
            character_id: ID of the character to associate with the image.
            
        Returns:
            Local path where the image was saved.
            
        Raises:
            HTTPException: If image download or saving fails.
        """
        try:
            # Create static/images directory if it doesn't exist
            os.makedirs("static/images", exist_ok=True)
            
            # Generate local path for the image
            image_path = f"static/images/character_{character_id}.png"
            
            # Download image using requests
            import requests
            try:
                logger.debug("Downloading image from: %s", image_url)
                response = requests.get(image_url, allow_redirects=True, verify=False)
                if response.status_code == 200:
                    with open(image_path, 'wb') as f:
                        f.write(response.content)
                    logger.info("Image saved locally: %s", image_path)
                    return image_path
                else:
                    error_msg = f"Failed to download image: {response.text}"
                    logger.error(error_msg)
                    raise HTTPException(status_code=response.status_code, detail=error_msg)
                    
            except Exception as e:
                error_msg = f"Failed to download image: {str(e)}\n{traceback.format_exc()}"
                logger.error(error_msg)
                raise HTTPException(status_code=500, detail=error_msg)
                
        except Exception as e:
            error_msg = f"Failed to save image: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg) 