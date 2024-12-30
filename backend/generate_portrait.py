import os
from fluxcli import FluxAPI
from PIL import Image

# Set the API key
os.environ["BFL_API_KEY"] = "47932f45-9b3d-4283-b525-92cca5a54f28"

def generate_portrait():
    print("Generating high-quality portrait...")
    api = FluxAPI(os.getenv("BFL_API_KEY"))
    
    # Generate the image
    image_url = api.generate_image(
        prompt="A photorealistic portrait of a handsome man with sharp features in a modern tailored black business suit, standing in a perfectly symmetrical front-facing pose, looking directly at the camera. Both arms held straight down at sides with palms facing the thighs, all ten fingers clearly visible and naturally extended. Shoulders perfectly squared to camera, body weight evenly distributed. Full length shot from head to toe capturing complete silhouette. Clean pure white background with subtle gradient lighting. Professional studio lighting setup with dramatic rim light to define edges and create depth. High-end fashion photography style, ultra-realistic details, 8k resolution, perfect composition with clear separation between subject and background",
        model="flux.1.1-ultra",
        aspect_ratio="9:16"  # Portrait orientation for full body shot
    )
    
    # Ensure output directory exists
    if not os.path.exists("outputs"):
        os.makedirs("outputs")
    
    # Save the image
    output_path = "outputs/portrait_man.jpg"
    if image_url:
        api.save_image_from_url(image_url, output_path)
        print(f"Image saved to {output_path}")

if __name__ == "__main__":
    generate_portrait()
