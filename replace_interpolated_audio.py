#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = ["moviepy>=2.0", "rich"]
# ///
"""
Replace audio in all interpolated videos: use original snippet audio first, 
then fill remaining time with goku.mp4 audio.

This script:
1. Extracts the first 8 seconds of audio from goku.mp4
2. Finds all video files in interpolated/{snippet_num}/ directories
3. For each interpolated video:
   - Finds the corresponding original snippet
   - Uses snippet audio for the first part
   - Fills remaining time with goku audio
4. Saves the updated videos back to the same location
"""

import json
import sys
from pathlib import Path
from moviepy import VideoFileClip, concatenate_audioclips

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.panel import Panel

console = Console()

INTERPOLATED_DIR = "interpolated"
SNIPPETS_DIR = "snippets"
SNIPPETS_INFO_FILE = "snippets/snippets_info.json"
GOKU_VIDEO = "goku.mp4"
AUDIO_DURATION = 8  # seconds


def get_goku_audio():
    """Extract and return the first 8 seconds of audio from goku.mp4."""
    if not Path(GOKU_VIDEO).exists():
        console.print(f"[red]❌ {GOKU_VIDEO} not found![/red]")
        return None
    
    try:
        goku_video = VideoFileClip(GOKU_VIDEO)
        if goku_video.audio is None:
            console.print(f"[yellow]⚠️  {GOKU_VIDEO} has no audio[/yellow]")
            goku_video.close()
            return None
        
        # Extract first 8 seconds of video (which includes audio)
        goku_clip = goku_video.subclipped(0, min(AUDIO_DURATION, goku_video.duration))
        # Return the clip itself, we'll extract audio when needed
        return goku_clip
    except Exception as e:
        console.print(f"[red]❌ Failed to load audio from {GOKU_VIDEO}: {e}[/red]")
        return None


def get_audio_for_duration(source_clip, target_duration: float):
    """Get audio trimmed or looped to match target duration."""
    source_duration = source_clip.duration
    
    if target_duration <= source_duration:
        # Trim to target duration
        trimmed_clip = source_clip.subclipped(0, target_duration)
        return trimmed_clip.audio
    else:
        # Loop audio to match target duration
        loops_needed = int(target_duration / source_duration) + 1
        audio_clips = []
        remaining_duration = target_duration
        
        for i in range(loops_needed):
            if remaining_duration <= 0:
                break
            take_duration = min(source_duration, remaining_duration)
            audio_subclip = source_clip.subclipped(0, take_duration)
            audio_clips.append(audio_subclip.audio)
            audio_subclip.close()
            remaining_duration -= take_duration
        
        if len(audio_clips) == 1:
            return audio_clips[0]
        else:
            concatenated = concatenate_audioclips(audio_clips)
            # Close individual audio clips
            for ac in audio_clips:
                ac.close()
            return concatenated


def load_snippets_info() -> dict:
    """Load snippets info and return a dict mapping snippet_number to snippet info."""
    if not Path(SNIPPETS_INFO_FILE).exists():
        console.print(f"[yellow]⚠️  {SNIPPETS_INFO_FILE} not found[/yellow]")
        return {}
    
    with open(SNIPPETS_INFO_FILE) as f:
        snippets = json.load(f)
    
    # Create mapping: snippet_number -> snippet_info
    return {s['snippet_number']: s for s in snippets}


def get_snippet_video_path(snippet_info: dict) -> Path:
    """Get the path to the original snippet video."""
    filename = snippet_info['filename']
    return Path(SNIPPETS_DIR) / filename


def get_snippet_number_from_path(video_path: Path) -> int | None:
    """Extract snippet number from interpolated video path."""
    # Path format: interpolated/{snippet_num:04d}/video_{start}_{end}.mp4
    try:
        snippet_dir = video_path.parent.name
        return int(snippet_dir)
    except (ValueError, AttributeError):
        return None


def find_all_interpolated_videos() -> list[Path]:
    """Find all video files in interpolated directories."""
    interpolated_path = Path(INTERPOLATED_DIR)
    
    if not interpolated_path.exists():
        return []
    
    video_files = []
    for snippet_dir in sorted(interpolated_path.iterdir()):
        if snippet_dir.is_dir():
            videos = list(snippet_dir.glob("*.mp4"))
            video_files.extend(videos)
    
    return video_files


def replace_video_audio(video_path: Path, goku_clip, snippets_info: dict) -> bool:
    """Replace audio: use snippet audio first, then fill with goku audio."""
    try:
        # Load interpolated video
        video = VideoFileClip(str(video_path))
        video_duration = video.duration
        
        # Find corresponding snippet
        snippet_num = get_snippet_number_from_path(video_path)
        if snippet_num is None or snippet_num not in snippets_info:
            console.print(f"   [yellow]⚠️  Could not find snippet for {video_path.name}, using goku audio only[/yellow]")
            # Fallback to goku audio only
            replacement_audio = get_audio_for_duration(goku_clip, video_duration)
        else:
            snippet_info = snippets_info[snippet_num]
            snippet_path = get_snippet_video_path(snippet_info)
            
            if snippet_path.exists():
                # Load snippet video and extract audio
                snippet_video = VideoFileClip(str(snippet_path))
                snippet_audio_duration = snippet_video.duration if snippet_video.audio else 0
                
                if snippet_video.audio and snippet_audio_duration > 0:
                    remaining_duration = video_duration - snippet_audio_duration
                    
                    if remaining_duration > 0:
                        # Use snippet audio first, then fill with goku audio
                        # Create subclip to properly extract audio
                        snippet_subclip = snippet_video.subclipped(0, min(snippet_audio_duration, snippet_video.duration))
                        snippet_audio = snippet_subclip.audio
                        
                        goku_audio = get_audio_for_duration(goku_clip, remaining_duration)
                        # Concatenate: snippet audio + goku audio
                        replacement_audio = concatenate_audioclips([snippet_audio, goku_audio])
                        
                        # Cleanup subclip and goku audio
                        snippet_subclip.close()
                        goku_audio.close()
                    else:
                        # Snippet audio is longer than video, trim it
                        trimmed_snippet = snippet_video.subclipped(0, video_duration)
                        replacement_audio = trimmed_snippet.audio
                        trimmed_snippet.close()
                    
                    # Close snippet video after audio is extracted
                    snippet_video.close()
                else:
                    # No snippet audio, use goku audio only
                    replacement_audio = get_audio_for_duration(goku_clip, video_duration)
                    snippet_video.close()
            else:
                # Snippet file not found, use goku audio only
                console.print(f"   [yellow]⚠️  Snippet file not found: {snippet_path}, using goku audio only[/yellow]")
                replacement_audio = get_audio_for_duration(goku_clip, video_duration)
        
        # Replace audio
        video_with_audio = video.with_audio(replacement_audio)
        
        # Write to temporary file first, then replace original
        temp_path = video_path.with_suffix('.tmp.mp4')
        video_with_audio.write_videofile(
            str(temp_path),
            codec='libx264',
            audio_codec='aac',
            logger=None,  # Suppress verbose output
        )
        
        # Cleanup
        video_with_audio.close()
        video.close()
        replacement_audio.close()
        
        # Replace original with new file
        temp_path.replace(video_path)
        
        return True
    except Exception as e:
        console.print(f"   [red]❌ Error processing {video_path.name}: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


def main():
    console.print(Panel.fit(
        "[bold cyan]🎵 REPLACE INTERPOLATED VIDEO AUDIO[/bold cyan]\n"
        "[white]Using snippet audio first, then filling with goku.mp4 audio[/white]",
        border_style="cyan"
    ))
    
    # Load snippets info
    console.print(f"\n[cyan]Loading snippets info...[/cyan]")
    snippets_info = load_snippets_info()
    console.print(f"[green]✓ Loaded {len(snippets_info)} snippet(s)[/green]")
    
    # Load goku audio clip
    console.print(f"[cyan]Loading audio from {GOKU_VIDEO}...[/cyan]")
    goku_clip = get_goku_audio()
    
    if goku_clip is None:
        console.print("[red]❌ Cannot proceed without goku audio[/red]")
        sys.exit(1)
    
    console.print(f"[green]✓ Goku audio loaded ({goku_clip.duration:.2f}s)[/green]\n")
    
    # Find all interpolated videos
    console.print("[cyan]Finding interpolated videos...[/cyan]")
    video_files = find_all_interpolated_videos()
    
    if not video_files:
        console.print("[yellow]⚠️  No interpolated videos found[/yellow]")
        goku_clip.close()
        sys.exit(0)
    
    console.print(f"[green]✓ Found {len(video_files)} video(s)[/green]\n")
    
    # Process each video
    success_count = 0
    fail_count = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Replacing audio...", total=len(video_files))
        
        for video_path in video_files:
            progress.update(task, description=f"[cyan]Processing {video_path.name}...")
            
            if replace_video_audio(video_path, goku_clip, snippets_info):
                success_count += 1
            else:
                fail_count += 1
            
            progress.advance(task)
    
    # Cleanup
    goku_clip.close()
    
    # Summary
    console.print()
    console.print(f"[green]✅ Successfully processed: {success_count}[/green]")
    if fail_count > 0:
        console.print(f"[red]❌ Failed: {fail_count}[/red]")
    console.print()


if __name__ == "__main__":
    main()

