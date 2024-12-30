#!/usr/bin/env python3
import os
import click
import json
from rich.console import Console
from rich.prompt import Prompt
from rich import print as rprint
from typing import Optional
import base64
from PIL import Image, ImageDraw
import requests
import io
import time
from io import BytesIO
import datetime

# Rich console for better formatting
console = Console()

class FluxAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("BFL_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set in BFL_API_KEY environment variable")
        self.base_url = "https://api.bfl.ml"
        self.headers = {"X-Key": self.api_key}
    
    def encode_image(self, image_path: str) -> str:
        """Convert an image file to base64 string."""
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def save_image_from_url(self, url: str, filename: str, target_width: int = None, target_height: int = None) -> bool:
        """Download and save image from URL."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            # Save the original image
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            # If target dimensions are specified, resize the image
            if target_width and target_height:
                with Image.open(filename) as img:
                    # Resize image maintaining aspect ratio
                    img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                    # Save resized image
                    img.save(filename, quality=95)
            
            console.print(f"[green]✨ Saved as {filename}")
            return True
        except Exception as e:
            console.print(f"[red]Failed to save image: {str(e)}")
            return False
    
    def get_task_result(self, task_id: str, silent: bool = False) -> Optional[dict]:
        """Poll for task result."""
        max_attempts = 30
        attempt = 0
        
        with console.status("[bold green]Processing image...") as status:
            while attempt < max_attempts:
                if not silent:
                    status.update(f"[bold green]Processing image... (attempt {attempt + 1}/{max_attempts})")
                
                response = requests.get(f"{self.base_url}/v1/get_result", params={'id': task_id})
                result = response.json()
                
                if result['status'] == 'Ready':
                    return result
                elif result['status'] == 'failed':
                    console.print(f"[red]Task failed: {result.get('error', 'Unknown error')}")
                    return None
                
                attempt += 1
                time.sleep(2)
        
        console.print("[red]Timeout waiting for result")
        return None

    def generate_image(self, prompt: str, model: str = "flux.1.1-pro", width: int = None, height: int = None, aspect_ratio: str = None) -> Optional[str]:
        """Generate an image using any FLUX model."""
        endpoint = {
            "flux.1.1-pro": "/v1/flux-pro-1.1",
            "flux.1-pro": "/v1/flux-pro",
            "flux.1-dev": "/v1/flux-dev",
            "flux.1.1-ultra": "/v1/flux-pro-1.1-ultra",
        }.get(model)
        
        if not endpoint:
            raise ValueError(f"Unknown model: {model}")
        
        # Set default dimensions based on aspect ratio if provided
        if aspect_ratio:
            if aspect_ratio == '1:1':
                width, height = 1024, 1024
            elif aspect_ratio == '4:3':
                width, height = 1024, 768
            elif aspect_ratio == '3:4':
                width, height = 768, 1024
            elif aspect_ratio == '16:9':
                width, height = 1024, 576
            elif aspect_ratio == '9:16':
                width, height = 576, 1024
        else:
            # Use defaults if neither aspect ratio nor dimensions are provided
            width = width or 1024
            height = height or 768
        
        payload = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "aspect_ratio": aspect_ratio if aspect_ratio else None
        }
        response = requests.post(
            f"{self.base_url}{endpoint}",
            json=payload,
            headers=self.headers
        )
        
        task_id = response.json().get('id')
        if not task_id:
            console.print("[red]Failed to start generation task")
            return None
            
        result = self.get_task_result(task_id)
        if result and result.get('result', {}).get('sample'):
            return result['result']['sample']
        return None

    def create_mask(self, size: tuple, shape: str = 'rectangle', position: str = 'center') -> Image:
        """Create a mask for inpainting."""
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        
        width, height = size
        
        if position == 'ground':
            # Find the horizon line (approximately where the car's wheels touch)
            horizon_y = height * 0.65  # Adjust this to match the car's position
            
            # Create a mask for the entire ground plane
            # Include some extra area above the horizon for better blending
            y_start = horizon_y - (height * 0.05)  # Start slightly above horizon
            
            # Create a polygon that covers the entire ground area
            points = [
                (0, y_start),          # Top left
                (0, height),           # Bottom left
                (width, height),       # Bottom right
                (width, y_start)       # Top right
            ]
            draw.polygon(points, fill=255)
        else:
            # Default center mask behavior
            x1 = width * 0.25
            y1 = height * 0.25
            x2 = width * 0.75
            y2 = height * 0.75
            
            if shape == 'rectangle':
                draw.rectangle([x1, y1, x2, y2], fill=255)
            else:  # circle
                center = (width // 2, height // 2)
                radius = min(width, height) // 4
                draw.ellipse([center[0] - radius, center[1] - radius,
                             center[0] + radius, center[1] + radius], fill=255)
        
        return mask

    def inpaint(self, image_path: str, prompt: str, mask_shape: str = 'circle', position: str = 'center') -> Optional[str]:
        """Inpaint an image using a mask."""
        # Load the base image and create mask
        base_image = Image.open(image_path)
        mask = self.create_mask(base_image.size, shape=mask_shape, position=position)
        
        # Save mask temporarily
        mask_path = 'temp_mask.jpg'
        mask.save(mask_path)
        
        payload = {
            "image": self.encode_image(image_path),
            "mask": self.encode_image(mask_path),
            "prompt": prompt,
            "steps": 50,
            "guidance": 60,
            "output_format": "jpeg",
            "safety_tolerance": 2
        }
        
        response = requests.post(
            f"{self.base_url}/v1/flux-pro-1.0-fill",
            json=payload,
            headers=self.headers
        )
        
        os.remove(mask_path)  # Clean up temporary mask file
        
        task_id = response.json().get('id')
        if not task_id:
            return None
            
        result = self.get_task_result(task_id)
        if result and result.get('result', {}).get('sample'):
            return result['result']['sample']
        return None

    def control_generate(self, control_type: str, control_image: str, prompt: str, **kwargs) -> Optional[str]:
        """Generate an image using any supported control type.
        
        Args:
            control_type: Type of control ('canny', 'depth', 'pose', etc.)
            control_image: Path to the control image
            prompt: Text prompt for generation
            **kwargs: Additional parameters for specific control types
        """
        # Map control types to their endpoints
        endpoints = {
            'canny': '/v1/flux-pro-1.0-canny',
            'depth': '/v1/flux-pro-1.0-depth',
            'pose': '/v1/flux-pro-1.0-pose'
        }
        
        # Map control types to their default parameters
        default_params = {
            'canny': {'guidance': 30},
            'depth': {'guidance': 15},
            'pose': {'guidance': 25}
        }
        
        if control_type not in endpoints:
            raise ValueError(f"Unsupported control type: {control_type}")
            
        # Start with default parameters for the control type
        payload = {
            "prompt": prompt,
            "control_image": self.encode_image(control_image),
            "steps": kwargs.get('steps', 50),
            "output_format": kwargs.get('output_format', 'jpeg'),
            "safety_tolerance": kwargs.get('safety_tolerance', 2)
        }
        
        # Add default parameters for the specific control type
        payload.update(default_params.get(control_type, {}))
        
        # Override with any provided kwargs
        payload.update(kwargs)
        
        response = requests.post(
            f"{self.base_url}{endpoints[control_type]}",
            json=payload,
            headers=self.headers
        )
        
        task_id = response.json().get('id')
        if not task_id:
            return None
            
        result = self.get_task_result(task_id)
        if result and result.get('result', {}).get('sample'):
            return result['result']['sample']
        return None

    # Update existing control methods to use the generic method
    def canny_control(self, control_image: str, prompt: str) -> Optional[str]:
        """Generate an image using Canny edge control."""
        return self.control_generate('canny', control_image, prompt)
    
    def depth_control(self, control_image: str, prompt: str) -> Optional[str]:
        """Generate an image using depth map control."""
        return self.control_generate('depth', control_image, prompt)
    
    def pose_control(self, control_image: str, prompt: str) -> Optional[str]:
        """Generate an image using pose control."""
        return self.control_generate('pose', control_image, prompt)

    def img2img(self, image_path: str, prompt: str, model: str = "flux.1.1-pro", strength: float = 0.75, width: int = None, height: int = None) -> Optional[str]:
        """Generate an image using another image as reference"""
        endpoint = {
            "flux.1.1-pro": "/v1/flux-pro-1.1",
            "flux.1-pro": "/v1/flux-pro",
            "flux.1-dev": "/v1/flux-dev",
            "flux.1.1-ultra": "/v1/flux-pro-1.1-ultra",
        }.get(model)
        
        if not endpoint:
            raise ValueError(f"Unknown model: {model}")
            
        # Read and encode the image
        with Image.open(image_path) as img:
            orig_width, orig_height = img.size
            
            # If dimensions not specified, use original image dimensions
            if width is None or height is None:
                width, height = orig_width, orig_height
            
            # Calculate aspect ratio
            aspect_ratio = orig_height / orig_width
            
            # Adjust dimensions to maintain aspect ratio while staying under limits
            total_pixels = width * height
            if total_pixels > 1048576:
                # Scale down while maintaining aspect ratio
                max_area = 1048576
                width = int((max_area / aspect_ratio) ** 0.5)
                height = int(width * aspect_ratio)
            
            # Convert image to base64
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=95)
            image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        payload = {
            "prompt": prompt,
            "image": image_base64,
            "strength": strength,
            "width": width,
            "height": height,
            "guidance_scale": 7.5,
            "num_inference_steps": 50,  # Increase steps for better quality
            "scheduler": "euler_ancestral",  # Use euler_ancestral scheduler for better results
            "preserve_init_image_color_profile": True  # Try to maintain original colors
        }
        
        response = requests.post(
            f"{self.base_url}{endpoint}",
            headers=self.headers,
            json=payload
        )
        
        task_id = response.json().get('id')
        if not task_id:
            console.print("[red]Failed to start image-to-image task")
            return None
            
        result = self.get_task_result(task_id)
        if result and result.get('result', {}).get('sample'):
            return result['result']['sample']
        return None

    def format_motion_prompt(self, name, base_prompt):
        """Format a prompt using the motion-based template structure"""
        # Define energy colors for different themes
        theme_colors = {
            "cyber": "neon",
            "mystic": "golden",
            "blade": "crimson",
            "mecha": "azure",
            "samurai": "crimson",
            "ninja": "shadow",
            "dragon": "emerald",
            "phoenix": "amber",
            "warrior": "scarlet",
            "pilot": "holographic"
        }
        
        # Determine the color based on keywords in the name
        energy_color = next((color for keyword, color in theme_colors.items() if keyword in name.lower()), "ethereal")
        
        # Create the motion-based prompt template
        motion_prompt = f"""Motion: The {energy_color} energy trails flow smoothly around the {name.replace('_', ' ')} in a continuous, fluid motion. The trails maintain their luminosity while gracefully circulating around the form, creating a sense of dynamic flow. The energy streams move at varying speeds - faster along the primary elements and slower around secondary details. The trails cast subtle, moving reflections on the surfaces, emphasizing key features. Background remains static while the energy trails create a constant, mesmerizing dance of light, suggesting both power and precision. The motion has a clear directional flow that emphasizes the overall form. {base_prompt}"""
        
        return motion_prompt

    def generate_motion_description(self, name: str, original_prompt: str) -> str:
        """Generate a motion-based description following the exact template format"""
        # Extract key themes from the name and prompt
        themes = {
            'mecha': {
                'color': 'cyan',
                'object': 'mecha',
                'surface': 'metallic plating',
                'trim': 'energy conduits',
                'flow': 'cockpit to extremities'
            },
            'cyber': {
                'color': 'neon blue',
                'object': 'cybernetic form',
                'surface': 'chrome chassis',
                'trim': 'circuit patterns',
                'flow': 'core to peripherals'
            },
            'mystic': {
                'color': 'ethereal gold',
                'object': 'mystic form',
                'surface': 'crystalline surface',
                'trim': 'runic patterns',
                'flow': 'center to aura'
            }
        }
        
        # Determine the theme based on name and prompt
        theme_key = next((key for key in themes.keys() if key in name.lower() or key in original_prompt.lower()), 'mystic')
        theme = themes[theme_key]
        
        # Generate description using exact format
        description = {
            "original_prompt": original_prompt,
            "motion_description": f"""Motion: The ethereal {theme['color']} energy trails flow smoothly around the {name} in a continuous, fluid motion. The trails maintain their luminosity while gracefully circulating around the {theme['object']}'s body, creating a sense of {theme_key} flow. The energy streams move at varying speeds - faster along the {theme['surface']} and slower around curves. The trails cast subtle, moving reflections on the {theme['surface']}, especially along the {theme['trim']}. Background remains static while the energy trails create a constant, mesmerizing dance of light, suggesting both power and elegance. The motion has a clear directional flow from {theme['flow']}, emphasizing its dynamic form."""
        }
        
        return description

    def save_metadata(self, name, prompt, image_path, model, strength=0.85):
        """Save generation metadata with the motion description"""
        # Generate the motion-based description
        motion_data = self.generate_motion_description(name, prompt)
        
        data = {
            "name": name,
            "original_prompt": prompt,
            "motion_description": motion_data["motion_description"],
            "image_path": image_path,
            "model": model,
            "strength": strength,
            "timestamp": "2024-12-09T15:50:13-06:00"
        }
        
        # Save in the prompts directory
        prompts_dir = os.path.join(os.path.dirname(image_path), "prompts")
        os.makedirs(prompts_dir, exist_ok=True)
        
        # Use timestamp in filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = os.path.join(prompts_dir, f"{name}_{timestamp}.json")
        
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=4)
        return json_path

@click.group()
@click.option('--api-key', envvar='BFL_API_KEY', help='FLUX API key')
@click.pass_context
def cli(ctx, api_key):
    """FLUX CLI - Image Generation Tool"""
    ctx.ensure_object(dict)
    ctx.obj['api'] = FluxAPI(api_key)

@cli.command()
@click.option('--prompt', '-p', required=True, help='Text prompt for image generation')
@click.option('--model', '-m', default='flux.1.1-pro', 
              type=click.Choice(['flux.1.1-pro', 'flux.1-pro', 'flux.1-dev', 'flux.1.1-ultra']),
              help='Model to use for generation')
@click.option('--aspect-ratio', '-ar', default=None, 
              type=click.Choice(['1:1', '4:3', '3:4', '16:9', '9:16']),
              help='Aspect ratio of the output image')
@click.option('--width', '-w', default=None, help='Image width (ignored if aspect-ratio is set)')
@click.option('--height', '-h', default=None, help='Image height (ignored if aspect-ratio is set)')
@click.option('--output', '-o', default='generated.jpg', help='Output filename')
@click.pass_context
def generate(ctx, prompt, model, aspect_ratio, width, height, output):
    """Generate an image from a text prompt"""
    api = ctx.obj['api']
    
    console.print(f"[green]Generating image with {model}...")
    console.print(f"Prompt: {prompt}")
    
    # Set default dimensions based on aspect ratio if provided
    if aspect_ratio:
        if aspect_ratio == '1:1':
            width, height = 1024, 1024
        elif aspect_ratio == '4:3':
            width, height = 1024, 768
        elif aspect_ratio == '3:4':
            width, height = 768, 1024
        elif aspect_ratio == '16:9':
            width, height = 1024, 576
        elif aspect_ratio == '9:16':
            width, height = 576, 1024
    else:
        # Use defaults if neither aspect ratio nor dimensions are provided
        width = width or 1024
        height = height or 768
    
    image_url = api.generate_image(
        prompt=prompt,
        model=model,
        width=width,
        height=height,
        aspect_ratio=aspect_ratio
    )
    
    if image_url:
        if api.save_image_from_url(image_url, output):
            console.print("[green]✨ Generation complete!")
        else:
            console.print("[red]Failed to save image")
    else:
        console.print("[red]Generation failed")

@cli.command()
@click.option('--image', '-i', required=True, help='Input image for inpainting')
@click.option('--prompt', '-p', required=True, help='Text prompt for inpainting')
@click.option('--mask-shape', '-m', type=click.Choice(['circle', 'rectangle']), default='circle',
              help='Shape of the mask')
@click.option('--position', '-pos', type=click.Choice(['center', 'ground']), default='center',
              help='Position of the mask')
@click.option('--output', '-o', default='inpainted.jpg', help='Output filename')
@click.pass_context
def inpaint(ctx, image, prompt, mask_shape, position, output):
    """Inpaint an image using a mask"""
    api = ctx.obj['api']
    
    console.print(f"[green]Inpainting image...")
    console.print(f"Prompt: {prompt}")
    
    image_url = api.inpaint(image, prompt, mask_shape, position)
    if image_url:
        if api.save_image_from_url(image_url, output):
            console.print("[green]✨ Inpainting complete!")
        else:
            console.print("[red]Failed to save image")
    else:
        console.print("[red]Inpainting failed")

@cli.command()
@click.option('--type', '-t', required=True, 
              type=click.Choice(['canny', 'depth', 'pose']),
              help='Type of control to use')
@click.option('--image', '-i', required=True, help='Input control image')
@click.option('--prompt', '-p', required=True, help='Text prompt for generation')
@click.option('--steps', default=50, help='Number of inference steps')
@click.option('--guidance', default=None, help='Guidance scale (uses default for control type if not specified)')
@click.option('--output', '-o', default=None, help='Output filename (defaults to control_type_result.jpg)')
@click.pass_context
def control(ctx, type, image, prompt, steps, guidance, output):
    """Generate an image using any supported control type."""
    api = ctx.obj['api']
    
    # Set default output filename if not provided
    if output is None:
        output = f"{type}_result.jpg"
    
    # Prepare kwargs
    kwargs = {'steps': steps}
    if guidance is not None:
        kwargs['guidance'] = guidance
    
    # Generate image
    result_url = api.control_generate(type, image, prompt, **kwargs)
    if not result_url:
        console.print("[red]Failed to generate image")
        return
    
    # Save the result
    api.save_image_from_url(result_url, output)

@cli.command()
@click.option('--image', '-i', required=True, help='Input image for image-to-image generation')
@click.option('--prompt', '-p', required=True, help='Text prompt for generation')
@click.option('--model', '-m', default='flux.1.1-pro', 
              type=click.Choice(['flux.1.1-pro', 'flux.1-pro', 'flux.1-dev', 'flux.1.1-ultra']),
              help='Model to use for generation')
@click.option('--strength', '-s', type=float, default=0.85, help='Generation strength (default: 0.85)')
@click.option('--width', '-w', default=None, type=int, help='Output image width')
@click.option('--height', '-h', default=None, type=int, help='Output image height')
@click.option('--output', '-o', default='outputs/generated.jpg', help='Output filename')
@click.option('--name', '-n', required=True, help='Name for the generation')
@click.pass_context
def img2img(ctx, image, prompt, model, strength, width, height, output, name):
    """Generate an image using another image as reference"""
    api = ctx.obj['api']
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output), exist_ok=True)
    
    console.print(f"[green]Generating image-to-image with {model}...")
    console.print(f"Input image: {image}")
    console.print(f"Prompt: {prompt}")
    
    # If width and height are not specified, get them from the input image
    if width is None or height is None:
        with Image.open(image) as img:
            width, height = img.size
    
    result = api.img2img(
        image_path=image,
        prompt=prompt,
        model=model,
        strength=strength,
        width=width,
        height=height
    )
    
    if result:
        image_url = result
        if api.save_image_from_url(image_url, output):
            # Save metadata in the same format as template prompts
            json_path = api.save_metadata(name, prompt, output, model, strength)
            console.print("[green]✨ Generation complete!")
            console.print(f"[blue]Metadata saved to: {json_path}")
        else:
            console.print("[red]Failed to save image")
    else:
        console.print("[red]Generation failed")

@cli.command()
@click.pass_context
def chat(ctx):
    """Start an interactive chat session for image generation"""
    console.print("[bold green]Welcome to FLUX Chat! 🎨")
    console.print("Type 'help' for commands or 'exit' to quit")
    
    api = ctx.obj['api']
    
    while True:
        try:
            command = Prompt.ask("\n[bold blue]What would you like to do?")
            
            if command.lower() == 'exit':
                break
            elif command.lower() == 'help':
                console.print("""
[bold]Available commands:[/bold]
- generate <prompt>: Generate an image
- ultra <prompt>: Use the Ultra model
- inpaint <image> <prompt>: Inpaint an existing image
- canny <image> <prompt>: Use Canny edge control
- depth <image> <prompt>: Use depth map control
- pose <image> <prompt>: Use pose control
- help: Show this help
- exit: Exit the chat
                """)
            elif command.lower().startswith('generate '):
                prompt = command[9:].strip()
                if prompt:
                    image_url = api.generate_image(prompt=prompt)
                    if image_url:
                        api.save_image_from_url(image_url, 'chat_generated.jpg')
                else:
                    console.print("[yellow]Please provide a prompt")
            elif command.lower().startswith('inpaint '):
                parts = command[8:].strip().split(' ', 1)
                if len(parts) == 2:
                    image, prompt = parts
                    image_url = api.inpaint(image, prompt)
                    if image_url:
                        api.save_image_from_url(image_url, 'chat_inpainted.jpg')
                else:
                    console.print("[yellow]Please provide both image path and prompt")
            elif command.lower().startswith('canny '):
                parts = command[6:].strip().split(' ', 1)
                if len(parts) == 2:
                    image, prompt = parts
                    image_url = api.canny_control(image, prompt)
                    if image_url:
                        api.save_image_from_url(image_url, 'chat_canny.jpg')
                else:
                    console.print("[yellow]Please provide both image path and prompt")
            elif command.lower().startswith('depth '):
                parts = command[6:].strip().split(' ', 1)
                if len(parts) == 2:
                    image, prompt = parts
                    image_url = api.depth_control(image, prompt)
                    if image_url:
                        api.save_image_from_url(image_url, 'chat_depth.jpg')
                else:
                    console.print("[yellow]Please provide both image path and prompt")
            elif command.lower().startswith('pose '):
                parts = command[5:].strip().split(' ', 1)
                if len(parts) == 2:
                    image, prompt = parts
                    image_url = api.pose_control(image, prompt)
                    if image_url:
                        api.save_image_from_url(image_url, 'chat_pose.jpg')
                else:
                    console.print("[yellow]Please provide both image path and prompt")
            else:
                console.print("[yellow]Unknown command. Type 'help' for available commands")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[red]Error: {str(e)}")
    
    console.print("\n[bold green]Thanks for using FLUX Chat! 👋")

if __name__ == '__main__':
    cli(obj={})
