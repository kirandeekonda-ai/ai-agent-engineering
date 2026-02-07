import os
import base64
import argparse
from groq import Groq
from dotenv import load_dotenv

# Load environment variables (assumes .env is in the root or current directory)
load_dotenv()

def encode_image(image_path):
    """Encodes a local image file to a base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def main():
    parser = argparse.ArgumentParser(description="Process images using Groq's Llama 3.2 Vision model.")
    parser.add_argument("--image", help="URL of the image or path to a local image file. Optional if you just want to chat.")
    parser.add_argument("--prompt", default="What's in this image?", help="Prompt for the model.")
    args = parser.parse_args()

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY not found in environment variables.")
        return

    client = Groq(api_key=api_key)
    model = "meta-llama/llama-4-scout-17b-16e-instruct"

    # specific logic for image provision
    content_payload = []
    
    # If image is provided, process it
    if args.image:
        image_input = args.image
        image_url_content = None

        if os.path.exists(image_input):
            # valid local file
            try:
                from PIL import Image
                import io
                try:
                    import pillow_avif
                except ImportError:
                    pass # Plugin not installed or not needed if supported natively
                
                # Load image with Pillow
                with Image.open(image_input) as img:
                    # Convert to RGB (in case of RGBA/P/etc)
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    
                    # Save as JPEG to a bytes buffer
                    buffered = io.BytesIO()
                    img.save(buffered, format="JPEG")
                    
                    # Encode the JPEG bytes
                    base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
                
                image_url_content = {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            except Exception as e:
                print(f"Error processing image file: {e}")
                return
        else:
            # Assume it's a URL
            image_url_content = {
                "url": image_input
            }
        
        # Add text and image to payload
        content_payload.append({"type": "text", "text": args.prompt})
        content_payload.append({"type": "image_url", "image_url": image_url_content})
    else:
        # Text-only mode
        # If no image is provided, use the prompt directly (and change default if needed, though CLI args handles default)
        # If user didn't provide a prompt and didn't provide an image, we should probably prompt them.
        if args.prompt == "What's in this image?":
            # User provided nothing
            print("Please provide an --image or a custom --prompt.")
            return
        
        content_payload.append({"type": "text", "text": args.prompt})

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": content_payload
                }
            ],
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        print(completion.choices[0].message.content)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
