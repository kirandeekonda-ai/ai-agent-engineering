# Week 22 - Multimodal Image Processing

This project contains a Python script to process images using Groq's Llama 3.2 Vision model.

## Setup

1.  **Environment Variables**: Ensure you have a `.env` file in the root or current directory with your `GROQ_API_KEY`.
2.  **Dependencies**: Install the required packages:
    ```bash
    pip install groq python-dotenv Pillow pillow-avif-plugin
    ```

## Usage

Run the script from the command line using `python image_processor.py`.

### Arguments

- `--image`: (Optional) The URL of an image OR a path to a local image file. Required if you want image analysis.
- `--prompt`: (Optional) The text prompt. REQUIRED if no image is provided. Defaults to "What's in this image?" if image is present.

### Examples

**1. Text-Only Chat:**

```bash
python image_processor.py --prompt "Tell me a short joke."
```

**2. Process an Image URL:**

```bash
python image_processor.py --image "https://upload.wikimedia.org/wikipedia/commons/f/f2/LPU-v1-die.jpg"
```

**2. Process a Local Image File:**

```bash
python image_processor.py --image "./image.png"
```

**3. Custom Prompt:**

```bash
python image_processor.py --image "./image.png" --prompt "Extract all text from this image."
```
