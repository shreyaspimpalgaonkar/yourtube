#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = ["graphon-client", "python-jose", "moviepy>=2.0", "numpy"]
# ///
"""
Video Query Script - Query your processed video with natural language
Run ingest_video.py first to process the video.

Usage:
    uv run query_video.py
"""

import asyncio
import json
import os
import re
from pathlib import Path

import numpy as np
from graphon_client import GraphonClient
from moviepy import VideoFileClip

# Configuration
CACHE_FILE = ".graphon_cache.json"
OUTPUT_DIR = "processed_videos"


def load_cache():
    """Load cached group_id."""
    if not Path(CACHE_FILE).exists():
        return None
    with open(CACHE_FILE, "r") as f:
        return json.load(f)


def format_time(seconds):
    """Format seconds as MM:SS."""
    if seconds is None:
        return "??:??"
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins}:{secs:02d}"


def sanitize_filename(text):
    """Convert query text to a valid filename."""
    clean = re.sub(r'[^\w\s-]', '', text.lower())
    clean = re.sub(r'[-\s]+', '_', clean).strip('_')
    return clean[:50] if len(clean) > 50 else clean


def add_green_glow(frame, t, segments):
    """Add green glow effect if current time is in a segment."""
    in_segment = False
    for seg in segments:
        start = seg.get("start_time", 0)
        end = seg.get("end_time", 0)
        if start <= t <= end:
            in_segment = True
            break
    
    if in_segment:
        frame = frame.copy().astype(np.int16)
        
        # Boost green channel
        frame[:, :, 1] = np.clip(frame[:, :, 1] + 40, 0, 255)
        
        # Add bright green border
        h, w = frame.shape[:2]
        border_size = 8
        
        # Top, bottom, left, right borders
        frame[:border_size, :, :] = [0, 255, 0]
        frame[-border_size:, :, :] = [0, 255, 0]
        frame[:, :border_size, :] = [0, 255, 0]
        frame[:, -border_size:, :] = [0, 255, 0]
        
        frame = frame.astype(np.uint8)
    
    return frame


def process_video_with_highlights(video_path, segments, query_text):
    """Add green glow effect to video segments and save."""
    if not segments:
        print("   ⚠️  No segments to highlight")
        return None
    
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    filename = sanitize_filename(query_text)
    output_path = Path(OUTPUT_DIR) / f"{filename}.mp4"
    
    print(f"\n🎬 Processing video with highlights...")
    print(f"   Input: {video_path}")
    print(f"   Output: {output_path}")
    print(f"   Segments: {len(segments)}")
    
    video = VideoFileClip(video_path)
    print(f"   Duration: {video.duration:.1f}s")
    
    def apply_glow(gf, t):
        frame = gf(t)
        return add_green_glow(frame, t, segments)
    
    video_with_glow = video.transform(apply_glow)
    
    print("   ⏳ Encoding video (this may take a minute)...")
    video_with_glow.write_videofile(
        str(output_path),
        codec='libx264',
        audio_codec='aac',
        logger='bar',
    )
    
    video.close()
    video_with_glow.close()
    
    print(f"\n✅ Saved to: {output_path}")
    return output_path


async def query(client, group_id, query_text):
    """Query the video and return results."""
    response = await client.query_group(
        group_id=group_id,
        query=query_text,
        return_source_data=True,
    )
    return response


async def main():
    print("\n" + "=" * 60)
    print("🔍 VIDEO QUERY - Powered by Graphon AI")
    print("=" * 60 + "\n")
    
    cache = load_cache()
    if not cache or not cache.get("group_id"):
        print("❌ No processed video found!")
        print("   Run 'uv run ingest_video.py' first.")
        return
    
    group_id = cache["group_id"]
    file_name = cache.get("file_name", "office.mp4")
    
    print(f"📁 Video: {file_name}")
    print(f"📦 Group ID: {group_id}")
    print(f"📂 Output: {OUTPUT_DIR}/\n")
    
    api_key = os.environ.get("GRAPHON_API_KEY")
    if not api_key:
        print("❌ ERROR: GRAPHON_API_KEY environment variable not set.")
        print("   Please set it with: export GRAPHON_API_KEY='your-api-key'")
        print("   Get an API key at https://graphon.ai")
        return
    
    client = GraphonClient(api_key=api_key)
    print("✅ Connected to Graphon API\n")
    
    print("💡 Example queries:")
    print("   • When does Michael Scott appear?")
    print("   • What happens during the fire drill?")
    print("   • When is Dwight on screen?")
    print("   • Find scenes with Andy Bernard")
    print("\nType 'quit' to exit.\n")
    print("-" * 60)
    
    while True:
        try:
            query_text = input("\n🎬 Query: ").strip()
            
            if not query_text:
                continue
            
            if query_text.lower() in ["quit", "exit", "q"]:
                print("\n👋 Goodbye!\n")
                break
            
            print(f"\n⏳ Searching...")
            
            response = await query(client, group_id, query_text)
            
            print(f"\n💬 Answer:\n{response.answer}")
            
            video_sources = [s for s in response.sources if s.get("node_type") == "video"]
            
            if video_sources:
                print(f"\n📍 Found {len(video_sources)} segment(s):")
                print("-" * 40)
                for i, source in enumerate(video_sources, 1):
                    start = source.get("start_time", 0)
                    end = source.get("end_time", 0)
                    print(f"   [{i}] {format_time(start)} → {format_time(end)}")
                print("-" * 40)
                
                process = input("\n🎨 Create highlighted video? (y/n): ").strip().lower()
                
                if process in ['y', 'yes']:
                    try:
                        process_video_with_highlights(file_name, video_sources, query_text)
                    except Exception as e:
                        print(f"\n❌ Video processing error: {e}")
            else:
                print("\n   No video segments found.")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
