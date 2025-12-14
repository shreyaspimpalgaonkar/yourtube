#!/usr/bin/env python3
"""
Create a simple 5-second video showing "Goku vs Vegeta" 
then "(sponsored video)" after 2 seconds.
"""

from moviepy import ColorClip, TextClip, CompositeVideoClip
from pathlib import Path

# Video settings
DURATION = 5  # seconds
WIDTH = 1920
HEIGHT = 1080
FPS = 24

# Text settings
FONT_SIZE_MAIN = 80
FONT_SIZE_SPONSORED = 60

# Output path
OUTPUT_DIR = Path("final_output")
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_PATH = OUTPUT_DIR / "goku_vs_vegeta_sponsored.mp4"


def create_sponsored_video():
    """Create a 5-second video with text overlays."""
    print("=" * 60)
    print("🎬 Creating Goku vs Vegeta Sponsored Video")
    print("=" * 60)
    
    # Create a black background
    background = ColorClip(
        size=(WIDTH, HEIGHT),
        color=(0, 0, 0),
        duration=DURATION
    )
    
    # Create "Goku vs Vegeta" text clip (shown for first 2 seconds)
    # Add margin to prevent text clipping at bottom
    main_text = TextClip(
        text="Goku vs Vegeta",
        font_size=FONT_SIZE_MAIN,
        color="white",
        method="caption",
        size=(int(WIDTH * 0.9), None),
        text_align="center",
        margin=(20, 20),  # Add padding top and bottom to prevent clipping
        duration=2,
    ).with_position("center")
    
    # Create "(sponsored video)" text clip (shown from 2s to 5s)
    sponsored_text = TextClip(
        text="(sponsored video)",
        font_size=FONT_SIZE_SPONSORED,
        color="yellow",
        method="caption",
        size=(int(WIDTH * 0.9), None),
        text_align="center",
        margin=(20, 20),  # Add padding top and bottom to prevent clipping
        duration=3,
    ).with_start(2).with_position("center")
    
    # Composite all clips together
    video = CompositeVideoClip(
        [background, main_text, sponsored_text],
        size=(WIDTH, HEIGHT)
    ).with_duration(DURATION)
    
    # Write the video file
    print(f"\n📹 Rendering video...")
    print(f"   Duration: {DURATION}s")
    print(f"   Resolution: {WIDTH}x{HEIGHT}")
    print(f"   Output: {OUTPUT_PATH}")
    
    video.write_videofile(
        str(OUTPUT_PATH),
        fps=FPS,
        codec="libx264",
        audio=False,  # No audio needed
        logger="bar",
    )
    
    # Cleanup
    video.close()
    background.close()
    main_text.close()
    sponsored_text.close()
    
    print(f"\n✅ Video created successfully!")
    print(f"   Saved to: {OUTPUT_PATH}")
    return OUTPUT_PATH


if __name__ == "__main__":
    try:
        create_sponsored_video()
    except Exception as e:
        print(f"\n❌ Error creating video: {e}")
        import traceback
        traceback.print_exc()

