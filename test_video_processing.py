#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = ["moviepy>=2.0", "numpy"]
# ///
"""
Test video processing with green glow highlights.
"""

import numpy as np
from pathlib import Path
from moviepy import VideoFileClip

# Test segments (from the query results)
TEST_SEGMENTS = [
    {"start_time": 20, "end_time": 25},
    {"start_time": 85, "end_time": 90},   # 1:25 → 1:30
    {"start_time": 35, "end_time": 40},
    {"start_time": 40, "end_time": 45},
    {"start_time": 45, "end_time": 50},
    {"start_time": 15, "end_time": 20},
    {"start_time": 25, "end_time": 30},
    {"start_time": 90, "end_time": 95},   # 1:30 → 1:35
    {"start_time": 30, "end_time": 35},
    {"start_time": 80, "end_time": 85},   # 1:20 → 1:25
]

VIDEO_FILE = "office.mp4"
OUTPUT_DIR = "processed_videos"


def add_green_glow(frame, t, segments):
    """Add green glow effect if current time is in a segment."""
    # Check if current time is in any segment
    in_segment = False
    for seg in segments:
        start = seg.get("start_time", 0)
        end = seg.get("end_time", 0)
        if start <= t <= end:
            in_segment = True
            break
    
    if in_segment:
        # Work with a copy
        frame = frame.copy().astype(np.int16)
        
        # Boost green channel
        frame[:, :, 1] = np.clip(frame[:, :, 1] + 40, 0, 255)
        
        # Add green border
        h, w = frame.shape[:2]
        border_size = 8
        
        # Create bright green border
        frame[:border_size, :, 0] = 0      # R
        frame[:border_size, :, 1] = 255    # G
        frame[:border_size, :, 2] = 0      # B
        
        frame[-border_size:, :, 0] = 0
        frame[-border_size:, :, 1] = 255
        frame[-border_size:, :, 2] = 0
        
        frame[:, :border_size, 0] = 0
        frame[:, :border_size, 1] = 255
        frame[:, :border_size, 2] = 0
        
        frame[:, -border_size:, 0] = 0
        frame[:, -border_size:, 1] = 255
        frame[:, -border_size:, 2] = 0
        
        frame = frame.astype(np.uint8)
    
    return frame


def process_video(video_path, segments, output_name):
    """Process video with green glow highlights."""
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    output_path = Path(OUTPUT_DIR) / f"{output_name}.mp4"
    
    print(f"\n🎬 Processing video...")
    print(f"   Input: {video_path}")
    print(f"   Output: {output_path}")
    print(f"   Segments to highlight: {len(segments)}")
    
    # Load video
    video = VideoFileClip(video_path)
    print(f"   Duration: {video.duration:.1f}s")
    print(f"   Size: {video.size}")
    
    # Apply green glow effect using fl (frame lambda)
    def apply_glow(gf, t):
        frame = gf(t)
        return add_green_glow(frame, t, segments)
    
    video_with_glow = video.transform(apply_glow)
    
    # Write output
    print("   ⏳ Encoding video...")
    video_with_glow.write_videofile(
        str(output_path),
        codec='libx264',
        audio_codec='aac',
        logger='bar',
    )
    
    # Cleanup
    video.close()
    video_with_glow.close()
    
    print(f"\n✅ Done! Saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TEST: Video Processing with Green Glow")
    print("=" * 60)
    
    if not Path(VIDEO_FILE).exists():
        print(f"❌ Video not found: {VIDEO_FILE}")
        exit(1)
    
    print(f"\n📍 Test segments:")
    for i, seg in enumerate(TEST_SEGMENTS, 1):
        start = seg["start_time"]
        end = seg["end_time"]
        print(f"   [{i}] {start//60}:{start%60:02d} → {end//60}:{end%60:02d}")
    
    process_video(VIDEO_FILE, TEST_SEGMENTS, "test_michael_scott_highlights")

