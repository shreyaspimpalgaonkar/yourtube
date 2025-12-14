#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = ["graphon-client", "python-jose"]
# ///
"""
Automated query script for Goku video
Finds timestamps with Goku and describes him in detail.
"""

import asyncio
import json
import os
from pathlib import Path

from graphon_client import GraphonClient

# Configuration
CACHE_FILE = ".graphon_cache.json"
QUERY = "Goku is an anime character from Dragon Ball Z. He is a young male fighter with distinctive spiky black hair that stands up in multiple points. He wears an iconic orange martial arts gi (uniform) with a blue undershirt visible underneath. He has blue wristbands on his arms, a blue belt or sash around his waist, and blue boots with yellow trim. On his chest or back, there is a circular white patch with a black kanji symbol (the Kame symbol, which looks like a turtle). He is muscular and athletic, often seen in fighting stances or flying through the air. He typically appears in rocky desert landscapes or clear blue skies. Find all accurate timestamps where Goku appears in this video."


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


async def query_goku():
    """Query the video for Goku timestamps and description."""
    print("\n" + "=" * 60)
    print("🔍 QUERYING GOKU VIDEO - Powered by Graphon AI")
    print("=" * 60 + "\n")
    
    cache = load_cache()
    if not cache or not cache.get("group_id"):
        print("❌ No processed video found!")
        print("   Run 'uv run ingest_video.py' first.")
        return
    
    group_id = cache["group_id"]
    file_name = cache.get("file_name", "goku.mp4")
    
    print(f"📁 Video: {file_name}")
    print(f"📦 Group ID: {group_id}\n")
    
    api_key = os.environ.get("GRAPHON_API_KEY")
    if not api_key:
        print("⚠️  GRAPHON_API_KEY environment variable not set.")
        print("   You can set it with: export GRAPHON_API_KEY='your-api-key'")
        print("   Or enter it when prompted below.")
        api_key = input("\nEnter your Graphon API key: ").strip()
        if not api_key:
            print("❌ API key required. Get one at https://graphon.ai")
            return
    
    client = GraphonClient(api_key=api_key)
    print("✅ Connected to Graphon API\n")
    
    print(f"🔍 Query: {QUERY}\n")
    print("⏳ Searching...\n")
    
    try:
        response = await client.query_group(
            group_id=group_id,
            query=QUERY,
            return_source_data=True,
        )
        
        print("=" * 60)
        print("💬 ANSWER:")
        print("=" * 60)
        print(f"\n{response.answer}\n")
        
        video_sources = [s for s in response.sources if s.get("node_type") == "video"]
        
        if video_sources:
            print("=" * 60)
            print(f"📍 FOUND {len(video_sources)} TIMESTAMP(S):")
            print("=" * 60)
            for i, source in enumerate(video_sources, 1):
                start = source.get("start_time", 0)
                end = source.get("end_time", 0)
                print(f"\n   [{i}] {format_time(start)} → {format_time(end)}")
                print(f"       ({start:.2f}s - {end:.2f}s)")
            print()
        else:
            print("\n   No video segments found.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(query_goku())

