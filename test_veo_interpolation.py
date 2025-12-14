#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = ["google-genai", "pillow"]
# ///
"""
Test Veo 3.1 interpolation with existing edited frames.
"""

import time
import io
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image

OUTPUT_DIR = "branded_video_output"

def main():
    print("🎬 Testing Veo 3.1 Interpolation")
    print("=" * 50)
    
    client = genai.Client()
    
    # Load the edited frames
    first_frame = Image.open(Path(OUTPUT_DIR) / "edited_first_frame.png")
    last_frame = Image.open(Path(OUTPUT_DIR) / "edited_last_frame.png")
    
    print(f"First frame: {first_frame.size}")
    print(f"Last frame: {last_frame.size}")
    
    # Convert to bytes
    first_bytes = io.BytesIO()
    first_frame.save(first_bytes, format='PNG')
    first_image = types.Image(image_bytes=first_bytes.getvalue(), mime_type="image/png")
    
    last_bytes = io.BytesIO()
    last_frame.save(last_bytes, format='PNG')
    last_image = types.Image(image_bytes=last_bytes.getvalue(), mime_type="image/png")
    
    prompt = """
    A smooth office scene video. Jim from The Office sits at his desk wearing a 
    white dress shirt with an Athlead sports marketing logo. He looks at his laptop 
    and slightly shifts his posture. The scene has natural office lighting and 
    maintains The Office's mockumentary style. Smooth, subtle motion.
    """
    
    print("\n📤 Sending to Veo 3.1...")
    
    try:
        operation = client.models.generate_videos(
            model="veo-3.1-generate-preview",
            prompt=prompt,
            image=first_image,
            config=types.GenerateVideosConfig(
                last_frame=last_image,
                duration_seconds="8",
                aspect_ratio="16:9",
            ),
        )
        
        print(f"Operation name: {operation.name}")
        print("⏳ Waiting for generation...")
        
        poll_count = 0
        while not operation.done:
            poll_count += 1
            print(f"   Polling... ({poll_count * 10}s)")
            time.sleep(10)
            operation = client.operations.get(operation)
        
        print("\n✅ Operation complete!")
        print(f"Response type: {type(operation.response)}")
        print(f"Response: {operation.response}")
        
        if operation.response and hasattr(operation.response, 'generated_videos'):
            videos = operation.response.generated_videos
            print(f"Generated videos: {videos}")
            
            if videos:
                video = videos[0]
                print(f"Video object: {video}")
                client.files.download(file=video.video)
                
                output_path = Path(OUTPUT_DIR) / "interpolated_video.mp4"
                video.video.save(str(output_path))
                print(f"\n✅ Saved to: {output_path}")
            else:
                print("No videos in response")
        else:
            print("No generated_videos attribute in response")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

