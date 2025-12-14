#!/usr/bin/env python3
"""
Interactive Video Query Script using Graphon API
Query the office.mp4 video to find character appearances and timestamps.
"""

import asyncio
import json
import os
from pathlib import Path

# Check if graphon-client is installed
try:
    from graphon_client import GraphonClient
except ImportError:
    print("Installing graphon-client...")
    os.system("pip install graphon-client")
    from graphon_client import GraphonClient

# Configuration
VIDEO_FILE = "office.mp4"
CACHE_FILE = ".graphon_cache.json"
GROUP_NAME = "Office Fire Drill Analysis"


def load_cache():
    """Load cached file_id and group_id if available."""
    if Path(CACHE_FILE).exists():
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_cache(data):
    """Save file_id and group_id to cache."""
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def format_time(seconds):
    """Format seconds as MM:SS."""
    if seconds is None:
        return "??:??"
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins}:{secs:02d}"


async def initialize_video(client, force_reprocess=False):
    """Upload and process the video, or use cached IDs."""
    cache = load_cache()
    
    # Check if we have valid cached data
    if not force_reprocess and cache.get("group_id"):
        print(f"📦 Found cached data for '{VIDEO_FILE}'")
        try:
            # Verify the group is still valid
            group = await client.get_group_status(cache["group_id"])
            if group.graph_status == "ready":
                print(f"✅ Using cached group: {cache['group_id']}")
                return cache["group_id"]
            else:
                print(f"⚠️  Cached group status: {group.graph_status}, re-processing...")
        except Exception as e:
            print(f"⚠️  Cached group invalid: {e}, re-processing...")
    
    # Need to process the video
    if not Path(VIDEO_FILE).exists():
        print(f"❌ Error: {VIDEO_FILE} not found in current directory!")
        print(f"   Current directory: {os.getcwd()}")
        return None
    
    print(f"\n🎬 Processing '{VIDEO_FILE}'...")
    print("   This may take several minutes for the first time.\n")
    
    def on_progress(step, current, total):
        if step == "uploading":
            print(f"   📤 Uploading: {current}/{total} files")
        elif step == "processing":
            print(f"   🔄 Processing: {current}/{total} files")
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
        })
        
        print(f"\n✅ Video processed successfully!")
        print(f"   Group ID: {group_id}")
        return group_id
        
    except Exception as e:
        print(f"\n❌ Error processing video: {e}")
        return None


async def query_video(client, group_id, query):
    """Query the video and display results."""
    print(f"\n🔍 Querying: \"{query}\"")
    print("-" * 50)
    
    try:
        response = await client.query_group(
            group_id=group_id,
            query=query,
            return_source_data=True,
        )
        
        # Print the answer
        print(f"\n💬 Answer:\n{response.answer}\n")
        
        # Print video segments
        video_sources = [s for s in response.sources if s.get("node_type") == "video"]
        
        if video_sources:
            print(f"📍 Found {len(video_sources)} relevant segment(s):\n")
            for i, source in enumerate(video_sources, 1):
                start = source.get("start_time", 0)
                end = source.get("end_time", 0)
                video_name = source.get("video_name", "video")
                print(f"   [{i}] {format_time(start)} - {format_time(end)}  ({video_name})")
            print()
        
        return response
        
    except Exception as e:
        print(f"❌ Query error: {e}")
        return None


async def interactive_mode(client, group_id):
    """Run interactive query loop."""
    print("\n" + "=" * 60)
    print("🎯 INTERACTIVE VIDEO QUERY MODE")
    print("=" * 60)
    print("\nExample queries:")
    print("  • When does Michael Scott appear?")
    print("  • What happens during the fire drill?")
    print("  • When is Dwight on screen?")
    print("  • Find all scenes with Andy Bernard")
    print("  • When do people panic?")
    print("\nType 'quit' or 'exit' to stop.\n")
    
    while True:
        try:
            query = input("🎬 Your query: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ["quit", "exit", "q"]:
                print("\n👋 Goodbye!")
                break
            
            if query.lower() == "clear":
                os.system("clear" if os.name == "posix" else "cls")
                continue
            
            if query.lower() == "reset":
                if Path(CACHE_FILE).exists():
                    os.remove(CACHE_FILE)
                print("🗑️  Cache cleared. Restart the script to re-process the video.")
                continue
            
            await query_video(client, group_id, query)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break


async def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("🎬 VIDEO QUERY TOOL - Powered by Graphon AI")
    print("=" * 60 + "\n")
    
    # Get API key
    api_key = os.environ.get("GRAPHON_API_KEY")
    
    if not api_key:
        print("⚠️  GRAPHON_API_KEY environment variable not set.")
        api_key = input("Enter your Graphon API key: ").strip()
        
        if not api_key:
            print("❌ API key required. Get one at https://graphon.ai")
            return
    
    # Initialize client
    client = GraphonClient(api_key=api_key)
    print("✅ Connected to Graphon API")
    
    # Initialize video
    group_id = await initialize_video(client)
    
    if not group_id:
        print("\n❌ Failed to initialize video. Please check the error above.")
        return
    
    # Run interactive mode
    await interactive_mode(client, group_id)


if __name__ == "__main__":
    asyncio.run(main())

