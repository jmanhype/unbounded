"""Test script for FLUX API."""
import os
import json
import asyncio
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
BFL_API_KEY = os.getenv("BFL_API_KEY")
if not BFL_API_KEY:
    raise ValueError("BFL_API_KEY environment variable is not set")

print(f"Using API key: {BFL_API_KEY}")

async def test_flux_api():
    """Test FLUX API with a simple image generation."""
    try:
        base_url = "https://api.bfl.ml"
        headers = {
            "X-Key": BFL_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Prepare payload
        payload = {
            "prompt": "A heroic warrior",
            "negative_prompt": "ugly, deformed",
            "width": 1024,
            "height": 1024,
            "model": "flux.1.1-pro",
            "steps": 50,
            "guidance": 7.5
        }
        
        print("\nSending request to FLUX API...")
        print("Headers:", json.dumps(headers, indent=2))
        print("Payload:", json.dumps(payload, indent=2))
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Start generation
            response = await client.post(
                f"{base_url}/v1/flux-pro-1.1",
                headers=headers,
                json=payload
            )
            
            print("\nGeneration Response:")
            print("Status:", response.status_code)
            print("Headers:", json.dumps(dict(response.headers), indent=2))
            print("Body:", response.text)
            
            if response.status_code != 200:
                print("\nError: Generation request failed")
                return
            
            result = response.json()
            task_id = result.get('id')
            
            if not task_id:
                print("\nError: No task ID in response")
                return
            
            print(f"\nTask ID: {task_id}")
            print("Polling for result...")
            
            # Poll for result
            max_attempts = 30
            attempt = 0
            
            while attempt < max_attempts:
                response = await client.get(
                    f"{base_url}/v1/get_result",
                    params={'id': task_id},
                    headers=headers
                )
                
                print(f"\nPoll attempt {attempt + 1}:")
                print("Status:", response.status_code)
                print("Body:", response.text)
                
                if response.status_code != 200:
                    print("\nError: Poll request failed")
                    return
                
                result = response.json()
                
                if result['status'] == 'Ready':
                    print("\nTask completed!")
                    print("Result:", json.dumps(result, indent=2))
                    return
                elif result['status'] == 'failed':
                    print("\nTask failed!")
                    print("Error:", result.get('error', 'Unknown error'))
                    return
                
                attempt += 1
                await asyncio.sleep(2)
            
            print("\nTimeout waiting for task completion")
            
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_flux_api()) 