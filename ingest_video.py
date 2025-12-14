#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = ["graphon-client", "python-jose"]
# ///
"""
Video Ingestion Script - Upload and process video with Graphon API
Run this once to process your video, then use query_video.py to query it.

Usage:
    uv run ingest_video.py
"""

import asyncio
import json
import os
from pathlib import Path

from graphon_client import GraphonClient

# Configuration
VIDEO_FILE = "goku.mp4"
CACHE_FILE = ".graphon_cache.json"
GROUP_NAME = "Goku Video Analysis"


def save_cache(data):
    """Save file_id and group_id to cache."""
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"💾 Saved cache to {CACHE_FILE}")


async def main():
    print("\n" + "=" * 60)
    print("🎬 VIDEO INGESTION - Powered by Graphon AI")
    print("=" * 60 + "\n")
    
    # Check if video exists
    if not Path(VIDEO_FILE).exists():
        print(f"❌ Error: {VIDEO_FILE} not found!")
        print(f"   Current directory: {os.getcwd()}")
        return
    
    # Get API key
    api_key = os.environ.get("GRAPHON_API_KEY")
    if not api_key:
        print("⚠️  GRAPHON_API_KEY environment variable not set.")
        print("   You can set it with: export GRAPHON_API_KEY='your-api-key'")
        print("   Or enter it when prompted below.")
        api_key = input("\nEnter your Graphon API key: ").strip()
        if not api_key:
            print("❌ API key required. Get one at https://graphon.ai")
            return
    
    # Initialize client
    client = GraphonClient(api_key=api_key)
    print("✅ Connected to Graphon API\n")
    
    print(f"📁 Video file: {VIDEO_FILE}")
    print(f"📊 File size: {Path(VIDEO_FILE).stat().st_size / (1024*1024):.1f} MB")
    print(f"📦 Group name: {GROUP_NAME}")
    print("\n" + "-" * 60)
    print("⏳ Starting upload and processing...")
    print("   This may take several minutes.\n")
    
    def on_progress(step, current, total):
        if step == "uploading":
            print(f"   📤 Uploading file {current}/{total}...")
        elif step == "processing":
            print(f"   🔄 Processing file {current}/{total}...")
        elif step == "building":
            print(f"   🏗️  Building knowledge graph...")
    
    try:
        group_id = await client.upload_process_and_create_group(
            file_paths=[VIDEO_FILE],
            group_name=GROUP_NAME,
            on_progress=on_progress,
        )
        
        # Save to cache
        save_cache({
            "file_name": VIDEO_FILE,
            "group_id": group_id,
            "group_name": GROUP_NAME,
        })
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS!")
        print("=" * 60)
        print(f"\n   Group ID: {group_id}")
        print(f"   Cache saved to: {CACHE_FILE}")
        print(f"\n🎯 Next step: Run 'uv run query_video.py' to query the video!\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
