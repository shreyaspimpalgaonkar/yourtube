#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = ["moviepy>=2.0", "google-genai", "pillow"]
# ///
"""
Brand Video Pipeline with consistent logo:
1. Generate a brand logo
2. Use the logo + frame to place it consistently
"""

import os
import io
from pathlib import Path
from moviepy import VideoFileClip
from google import genai
from google.genai import types
from PIL import Image

# Configuration
VIDEO_FILE = "office.mp4"
OUTPUT_DIR = "branded_video_output"

# Jim segment: 0:16 to 0:20 (in seconds)
START_TIME = 16
END_TIME = 20


def generate_logo(client: genai.Client, brand_name: str) -> Image.Image:
    """Generate a brand logo using Gemini."""
    print(f"🎨 Generating {brand_name} logo...")
    
    logo_prompt = f"""
    Create a professional sports marketing company logo for "{brand_name}".
    The logo should be:
    - Clean and modern design
    - Include the text "{brand_name}" prominently
    - Have a dynamic sports-related icon (like a running figure or stylized 'A')
    - Use blue and white/silver colors
    - Suitable for embroidery on a shirt
    - On a transparent or white background
    - High quality, vector-style appearance
    
    Make it look like a real professional sports agency logo.
    """
    
    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[logo_prompt],
    )
    
    for part in response.parts:
        if part.inline_data is not None:
            image_data = part.inline_data.data
            logo = Image.open(io.BytesIO(image_data))
            print("   ✅ Logo generated!")
            return logo
        elif part.text is not None:
            print(f"   Note: {part.text[:100]}...")
    
    raise ValueError("Failed to generate logo")


def extract_frame(video_path: str, timestamp: float) -> Image.Image:
    """Extract a single frame from video."""
    video = VideoFileClip(video_path)
    frame = video.get_frame(timestamp)
    video.close()
    return Image.fromarray(frame)


def add_logo_to_frame(client: genai.Client, frame: Image.Image, logo: Image.Image) -> Image.Image:
    """Add logo to frame with consistent positioning."""
    
    # Convert frame to bytes
    frame_bytes = io.BytesIO()
    frame.save(frame_bytes, format='PNG')
    frame_part = types.Part.from_bytes(data=frame_bytes.getvalue(), mime_type='image/png')
    
    # Convert logo to bytes
    logo_bytes = io.BytesIO()
    logo.save(logo_bytes, format='PNG')
    logo_part = types.Part.from_bytes(data=logo_bytes.getvalue(), mime_type='image/png')
    
    # Precise positioning prompt
    prompt = """
    I'm providing two images:
    1. First image: A frame from The Office showing a person in a white dress shirt
    2. Second image: An Athlead logo
    
    Please edit the first image to add the Athlead logo from the second image onto the shirt.
    
    POSITIONING REQUIREMENTS (VERY IMPORTANT):
    - Place the logo on the LEFT side of the chest (viewer's right)
    - Position it just ABOVE the pocket area
    - The logo should be about 2-3 inches in size (proportional to the shirt)
    - Make it look like an embroidered or printed logo on the fabric
    - The logo should follow the natural folds and contours of the shirt
    
    Keep everything else EXACTLY the same - face, expression, background, lighting.
    Only add the logo in the specified position.
    """
    
    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[frame_part, logo_part, prompt],
    )
    
    for part in response.parts:
        if part.inline_data is not None:
            image_data = part.inline_data.data
            edited = Image.open(io.BytesIO(image_data))
            return edited
        elif part.text is not None:
            print(f"   Note: {part.text[:100]}...")
    
    raise ValueError("Failed to add logo to frame")


def main():
    print("=" * 70)
    print("🎬 BRAND VIDEO PIPELINE: Consistent Logo Placement")
    print("=" * 70)
    
    if not Path(VIDEO_FILE).exists():
        print(f"❌ Video not found: {VIDEO_FILE}")
        return
    
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    
    client = genai.Client()
    
    # Step 1: Generate the Athlead logo
    print("\n[Step 1/4] Generating Athlead logo...")
    logo = generate_logo(client, "Athlead")
    logo_path = Path(OUTPUT_DIR) / "athlead_logo.png"
    logo.save(logo_path)
    print(f"   Saved logo to: {logo_path}")
    
    # Step 2: Extract frames
    print(f"\n[Step 2/4] Extracting frames from segment {START_TIME}s to {END_TIME}s...")
    first_frame = extract_frame(VIDEO_FILE, START_TIME)
    last_frame = extract_frame(VIDEO_FILE, END_TIME)
    
    first_frame.save(Path(OUTPUT_DIR) / "original_first_frame.png")
    last_frame.save(Path(OUTPUT_DIR) / "original_last_frame.png")
    print("   ✅ Frames extracted")
    
    # Step 3: Add logo to frames with consistent positioning
    print("\n[Step 3/4] Adding logo to frames with consistent positioning...")
    
    print("   Processing first frame...")
    edited_first = add_logo_to_frame(client, first_frame, logo)
    edited_first.save(Path(OUTPUT_DIR) / "edited_first_frame.png")
    print("   ✅ First frame branded")
    
    print("   Processing last frame...")
    edited_last = add_logo_to_frame(client, last_frame, logo)
    edited_last.save(Path(OUTPUT_DIR) / "edited_last_frame.png")
    print("   ✅ Last frame branded")
    
    # Step 4: Summary
    print("\n[Step 4/4] Complete!")
    print(f"\n✅ Output files in '{OUTPUT_DIR}/':")
    print(f"   - athlead_logo.png (the generated logo)")
    print(f"   - original_first_frame.png")
    print(f"   - original_last_frame.png")
    print(f"   - edited_first_frame.png")
    print(f"   - edited_last_frame.png")
    
    print("\n🎉 Done! Consistent branding applied to both frames.")


if __name__ == "__main__":
    main()

