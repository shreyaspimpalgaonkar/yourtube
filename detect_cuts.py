#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = ["moviepy>=2.0", "numpy", "opencv-python"]
# ///
"""
Detect scene cuts in a video and split into snippets.
Uses frame difference analysis to detect hard cuts.

Usage:
    uv run detect_cuts.py
"""

import cv2
import numpy as np
from pathlib import Path
import subprocess
import json

# Configuration
VIDEO_FILE = "goku.mp4"
OUTPUT_DIR = "snippets"
THRESHOLD = 30.0  # Difference threshold for cut detection (adjustable)
MIN_SCENE_FRAMES = 10  # Minimum frames between cuts to avoid false positives


def get_video_info(video_path):
    """Get video metadata using OpenCV."""
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps if fps > 0 else 0
    cap.release()
    return {
        "fps": fps,
        "total_frames": total_frames,
        "width": width,
        "height": height,
        "duration": duration
    }


def compute_frame_difference(frame1, frame2):
    """Compute the mean absolute difference between two frames."""
    if frame1 is None or frame2 is None:
        return 0
    
    # Convert to grayscale for faster comparison
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    
    # Compute absolute difference
    diff = cv2.absdiff(gray1, gray2)
    return np.mean(diff)


def detect_scene_cuts(video_path, threshold=THRESHOLD, min_scene_frames=MIN_SCENE_FRAMES):
    """Detect scene cuts in a video by analyzing frame differences."""
    print(f"\n🔍 Analyzing video for scene cuts...")
    print(f"   Threshold: {threshold}")
    print(f"   Min scene frames: {min_scene_frames}")
    
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    cuts = []
    differences = []
    prev_frame = None
    frame_idx = 0
    last_cut_frame = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if prev_frame is not None:
            diff = compute_frame_difference(prev_frame, frame)
            differences.append((frame_idx, diff))
            
            # Check if this is a cut (high difference and enough frames since last cut)
            if diff > threshold and (frame_idx - last_cut_frame) >= min_scene_frames:
                cuts.append(frame_idx)
                last_cut_frame = frame_idx
                print(f"   📍 Cut detected at frame {frame_idx} (diff: {diff:.2f})")
        
        prev_frame = frame.copy()
        frame_idx += 1
        
        # Progress indicator
        if frame_idx % 100 == 0:
            pct = (frame_idx / total_frames) * 100
            print(f"   Analyzing... {pct:.1f}% ({frame_idx}/{total_frames} frames)", end='\r')
    
    cap.release()
    print(f"\n   ✅ Analysis complete. Found {len(cuts)} cuts.")
    
    return cuts, differences, fps, total_frames


def split_video_at_cuts(video_path, cuts, fps, total_frames, output_dir):
    """Split video into snippets at cut points using ffmpeg."""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Create segments list (start_frame, end_frame)
    segments = []
    
    # First segment starts at frame 0
    start_frame = 0
    for cut_frame in cuts:
        # End the previous segment just before the cut
        end_frame = cut_frame - 1
        if end_frame > start_frame:
            segments.append((start_frame, end_frame))
        start_frame = cut_frame
    
    # Last segment goes to the end
    if start_frame < total_frames - 1:
        segments.append((start_frame, total_frames - 1))
    
    print(f"\n📦 Splitting video into {len(segments)} snippets...")
    
    snippet_info = []
    for i, (start, end) in enumerate(segments, 1):
        # Convert frames to time
        start_time = start / fps
        end_time = (end + 1) / fps  # +1 to include the end frame
        duration = end_time - start_time
        
        # Create filename: 0001_startframe_endframe.mp4
        output_name = f"{i:04d}_{start}_{end}.mp4"
        output_path = output_dir / output_name
        
        print(f"   [{i}/{len(segments)}] Frames {start}-{end} → {output_name}")
        
        # Use ffmpeg to extract the snippet
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),
            "-i", str(video_path),
            "-t", str(duration),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-avoid_negative_ts", "1",
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"      ⚠️  Warning: ffmpeg returned {result.returncode}")
        
        snippet_info.append({
            "snippet_number": i,
            "filename": output_name,
            "start_frame": start,
            "end_frame": end,
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration
        })
    
    return snippet_info


def main():
    print("\n" + "=" * 60)
    print("🎬 VIDEO SCENE CUT DETECTION & SPLITTING")
    print("=" * 60)
    
    video_path = Path(VIDEO_FILE)
    if not video_path.exists():
        print(f"❌ Error: {VIDEO_FILE} not found!")
        return
    
    # Get video info
    info = get_video_info(video_path)
    print(f"\n📊 Video Info:")
    print(f"   File: {VIDEO_FILE}")
    print(f"   Resolution: {info['width']}x{info['height']}")
    print(f"   FPS: {info['fps']:.2f}")
    print(f"   Total frames: {info['total_frames']}")
    print(f"   Duration: {info['duration']:.2f}s")
    
    # Detect cuts
    cuts, differences, fps, total_frames = detect_scene_cuts(video_path)
    
    # Print detected cuts
    print(f"\n📍 Detected Cut Frames:")
    for i, cut in enumerate(cuts, 1):
        time_sec = cut / fps
        print(f"   [{i}] Frame {cut} (time: {time_sec:.2f}s)")
    
    # Create output directory
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    
    # Save cut info to JSON for reference
    cut_info = {
        "video_file": VIDEO_FILE,
        "fps": fps,
        "total_frames": total_frames,
        "cuts": cuts,
        "cut_times": [cut / fps for cut in cuts]
    }
    
    with open(Path(OUTPUT_DIR) / "cuts_info.json", "w") as f:
        json.dump(cut_info, f, indent=2)
    
    # Split video
    snippets = split_video_at_cuts(video_path, cuts, fps, total_frames, OUTPUT_DIR)
    
    # Save snippet info
    with open(Path(OUTPUT_DIR) / "snippets_info.json", "w") as f:
        json.dump(snippets, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ COMPLETE!")
    print("=" * 60)
    print(f"\n📁 Output directory: {OUTPUT_DIR}/")
    print(f"   - {len(snippets)} video snippets")
    print(f"   - cuts_info.json (cut frame data)")
    print(f"   - snippets_info.json (snippet details)")
    print(f"\n💡 Review the snippets and label them as needed!")


if __name__ == "__main__":
    main()

