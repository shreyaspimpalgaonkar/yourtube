#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = ["moviepy>=2.0", "rich"]
# ///
"""
Merge processed/interpolated videos with original snippets to create final branded video.

For each snippet:
- If processed videos exist in interpolated/{snippet_num}/, concatenate them and use that
- Otherwise, use the original snippet

Then merge all snippets in order to create the final video.

Usage: uv run merge_branded_video.py [--output OUTPUT_PATH]
"""

import json
import sys
import subprocess
import tempfile
from pathlib import Path
from moviepy import VideoFileClip, concatenate_videoclips, AudioFileClip

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.table import Table

console = Console()

SNIPPETS_DIR = "snippets"
INTERPOLATED_DIR = "interpolated"
OUTPUT_DIR = "final_output"
SNIPPETS_INFO_FILE = "snippets/snippets_info.json"
GOKU_VIDEO = "goku.mp4"
SPONSORED_VIDEO = "final_output/goku_vs_vegeta_sponsored.mp4"


def find_processed_videos(snippet_num: int) -> list[Path]:
    """Find all processed/interpolated videos for a snippet, sorted by index.
    Prefers _trimmed.mp4 files if they exist."""
    interpolated_dir = Path(INTERPOLATED_DIR) / f"{snippet_num:04d}"
    
    if not interpolated_dir.exists():
        return []
    
    # Find all video files matching pattern: {idx:04d}_{frame_start}_{frame_end}.mp4
    video_files = list(interpolated_dir.glob("*.mp4"))
    
    if not video_files:
        return []
    
    # Prefer _trimmed.mp4 files over originals
    trimmed_files = {f for f in video_files if "_trimmed.mp4" in f.name}
    if trimmed_files:
        # Use trimmed files only
        video_files = list(trimmed_files)
    
    # Sort by the index prefix (first part before underscore)
    def get_index(path: Path) -> int:
        try:
            # Extract index from filename like "0000_119_142.mp4" or "video_0000_119_142_trimmed.mp4"
            stem = path.stem.replace("_trimmed", "")  # Remove _trimmed suffix
            if stem.startswith("interpolated_"):
                index_str = stem.split('_')[1]
            elif stem.startswith("video_"):
                # Handle "video_0000_119_142" format
                parts = stem.split('_')
                if len(parts) > 1:
                    index_str = parts[1]
                else:
                    index_str = parts[0]
            else:
                index_str = stem.split('_')[0]
            return int(index_str)
        except (ValueError, IndexError):
            return 999999  # Put malformed filenames at the end
    
    video_files.sort(key=get_index)
    return video_files


def get_snippet_video_path(snippet_info: dict) -> Path:
    """Get the path to the original snippet video."""
    filename = snippet_info['filename']
    return Path(SNIPPETS_DIR) / filename


def get_goku_audio_source():
    """Load and return the first 8 seconds of audio from goku.mp4."""
    if not Path(GOKU_VIDEO).exists():
        console.print(f"[yellow]⚠️  {GOKU_VIDEO} not found, skipping audio replacement[/yellow]")
        return None
    
    try:
        goku_video = VideoFileClip(GOKU_VIDEO)
        if goku_video.audio is None:
            console.print(f"[yellow]⚠️  {GOKU_VIDEO} has no audio, skipping audio replacement[/yellow]")
            goku_video.close()
            return None
        
        # Extract first 8 seconds of video (which includes audio)
        goku_clip = goku_video.subclipped(0, min(8.0, goku_video.duration))
        return goku_clip
    except Exception as e:
        console.print(f"[yellow]⚠️  Failed to load audio from {GOKU_VIDEO}: {e}[/yellow]")
        return None


def replace_veo_audio(clip: VideoFileClip, goku_clip: VideoFileClip, snippet_info: dict = None, target_duration: float = None) -> VideoFileClip:
    """Replace Veo video audio: use snippet audio first, then fill with goku audio.
    
    Args:
        clip: Video clip to replace audio for
        goku_clip: Source clip with goku audio (first 8 seconds)
        snippet_info: Info about the original snippet
        target_duration: Target duration for the audio (if None, uses clip.duration)
    """
    if goku_clip is None or goku_clip.audio is None:
        return clip
    
    try:
        # Use target_duration if provided (for trimming), otherwise use clip duration
        clip_duration = target_duration if target_duration is not None else clip.duration
        
        # Try to get snippet audio first
        snippet_audio = None
        snippet_audio_duration = 0
        
        snippet_video = None
        snippet_subclip = None
        goku_subclip = None
        
        if snippet_info:
            snippet_path = get_snippet_video_path(snippet_info)
            if snippet_path.exists():
                try:
                    snippet_video = VideoFileClip(str(snippet_path))
                    if snippet_video.audio:
                        snippet_audio_duration = snippet_video.duration
                except Exception as e:
                    console.print(f"[yellow]⚠️  Failed to load snippet audio: {e}[/yellow]")
        
        remaining_duration = clip_duration - snippet_audio_duration
        
        if snippet_audio_duration > 0 and remaining_duration > 0:
            # Write full audio files to temp files first
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_snippet:
                temp_snippet_path = temp_snippet.name
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_goku:
                temp_goku_path = temp_goku.name
            
            # Write full audio files while videos are open
            # Check that audio readers are valid before writing
            snippet_audio_valid = False
            goku_audio_valid = False
            
            if snippet_video and snippet_video.audio:
                try:
                    # Verify audio reader is valid
                    _ = snippet_video.audio.duration
                    if hasattr(snippet_video.audio, 'reader'):
                        snippet_audio_valid = True
                except:
                    pass
            
            if goku_clip and goku_clip.audio:
                try:
                    # Verify audio reader is valid
                    _ = goku_clip.audio.duration
                    if hasattr(goku_clip.audio, 'reader'):
                        goku_audio_valid = True
                except:
                    pass
            
            if not snippet_audio_valid:
                console.print(f"[yellow]⚠️  Snippet audio reader invalid, using goku audio only[/yellow]")
                if snippet_video:
                    snippet_video.close()
                if goku_audio_valid:
                    goku_clip.audio.write_audiofile(temp_goku_path, logger=None)
                    goku_audio_file_full = AudioFileClip(temp_goku_path)
                    goku_audio_file = goku_audio_file_full.subclipped(0, min(clip_duration, goku_audio_file_full.duration))
                    replacement_audio = goku_audio_file
                    goku_audio_file_full.close()
                    return clip.with_audio(replacement_audio)
                else:
                    # No valid audio, return clip without audio replacement
                    if snippet_video:
                        snippet_video.close()
                    return clip
            
            if not goku_audio_valid:
                console.print(f"[yellow]⚠️  Goku audio reader invalid, using snippet audio only[/yellow]")
                if snippet_audio_valid:
                    snippet_video.audio.write_audiofile(temp_snippet_path, logger=None)
                    snippet_audio_file_full = AudioFileClip(temp_snippet_path)
                    snippet_audio_file = snippet_audio_file_full.subclipped(0, min(clip_duration, snippet_audio_file_full.duration))
                    replacement_audio = snippet_audio_file
                    snippet_audio_file_full.close()
                    if snippet_video:
                        snippet_video.close()
                    return clip.with_audio(replacement_audio)
                else:
                    # No valid audio, return clip without audio replacement
                    if snippet_video:
                        snippet_video.close()
                    return clip
            
            # Both audio sources are valid, proceed with writing
            # Initialize audio readers by accessing duration first
            try:
                _ = snippet_video.audio.duration
                snippet_video.audio.write_audiofile(temp_snippet_path, logger=None)
            except Exception as e:
                console.print(f"[yellow]⚠️  Failed to write snippet audio: {e}, using goku audio only[/yellow]")
                if snippet_video:
                    snippet_video.close()
                try:
                    _ = goku_clip.audio.duration
                    goku_clip.audio.write_audiofile(temp_goku_path, logger=None)
                    goku_audio_file_full = AudioFileClip(temp_goku_path)
                    goku_audio_file = goku_audio_file_full.subclipped(0, min(clip_duration, goku_audio_file_full.duration))
                    replacement_audio = goku_audio_file
                    goku_audio_file_full.close()
                    return clip.with_audio(replacement_audio)
                except Exception as e2:
                    console.print(f"[yellow]⚠️  Failed to write goku audio: {e2}, keeping original audio[/yellow]")
                    if snippet_video:
                        snippet_video.close()
                    return clip
            
            try:
                _ = goku_clip.audio.duration
                goku_clip.audio.write_audiofile(temp_goku_path, logger=None)
            except Exception as e:
                console.print(f"[yellow]⚠️  Failed to write goku audio: {e}, using snippet audio only[/yellow]")
                snippet_audio_file_full = AudioFileClip(temp_snippet_path)
                snippet_audio_file = snippet_audio_file_full.subclipped(0, min(clip_duration, snippet_audio_file_full.duration))
                replacement_audio = snippet_audio_file
                snippet_audio_file_full.close()
                if snippet_video:
                    snippet_video.close()
                return clip.with_audio(replacement_audio)
            
            # Now close videos - we have the audio files
            if snippet_video:
                snippet_video.close()
            
            # Load audio files and trim them
            snippet_audio_file_full = AudioFileClip(temp_snippet_path)
            goku_audio_file_full = AudioFileClip(temp_goku_path)
            
            # Trim to correct durations
            snippet_audio_file = snippet_audio_file_full.subclipped(0, min(snippet_audio_duration, snippet_audio_file_full.duration))
            goku_audio_file = goku_audio_file_full.subclipped(0, min(remaining_duration, goku_audio_file_full.duration))
            
            # Use ffmpeg to concatenate audio files (more reliable than moviepy concatenate)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as concat_list:
                concat_list_path = concat_list.name
                # Write ffmpeg concat file format
                concat_list.write(f"file '{temp_snippet_path}'\n")
                concat_list.write(f"file '{temp_goku_path}'\n")
            
            # Output file for concatenated audio
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_final:
                temp_final_path = temp_final.name
            
            # Use ffmpeg to concatenate audio files
            try:
                subprocess.run(
                    ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', concat_list_path, 
                     '-c', 'copy', '-y', temp_final_path],
                    check=True,
                    capture_output=True,
                    stderr=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL
                )
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                # Fallback to moviepy concatenation if ffmpeg fails
                console.print(f"[yellow]⚠️  ffmpeg concat failed, using moviepy: {e}[/yellow]")
                from moviepy import concatenate_audioclips
                concatenated_temp = concatenate_audioclips([snippet_audio_file, goku_audio_file])
                concatenated_temp.write_audiofile(temp_final_path, logger=None)
                concatenated_temp.close()
            
            # Now load the final audio file
            replacement_audio = AudioFileClip(temp_final_path)
            
            # Close intermediate resources
            snippet_audio_file.close()
            goku_audio_file.close()
            snippet_audio_file_full.close()
            goku_audio_file_full.close()
        elif snippet_audio and snippet_audio_duration >= clip_duration:
            # Snippet audio is longer, trim it
            if snippet_subclip:
                snippet_subclip.close()
            if snippet_video:
                snippet_video.close()
            # Reload snippet video to get trimmed audio
            snippet_path = get_snippet_video_path(snippet_info)
            snippet_video = VideoFileClip(str(snippet_path))
            snippet_subclip = snippet_video.subclipped(0, clip_duration)
            replacement_audio = snippet_subclip.audio
            snippet_subclip.close()
            snippet_video.close()
            snippet_audio.close()
        else:
            # No snippet audio, use first clip_duration seconds of goku audio only
            # (which is the first (8 - 0) = 8 seconds for interpolated videos)
            goku_subclip = goku_clip.subclipped(0, min(clip_duration, goku_clip.duration))
            replacement_audio = goku_subclip.audio
            goku_subclip.close()
        
        # Replace audio using with_audio method
        clip_with_new_audio = clip.with_audio(replacement_audio)
        
        # Don't close replacement_audio here - it's now attached to the video clip
        # The video clip will handle cleanup when it's written/closed
        # If replacement_audio is from a temp file, it will be cleaned up when the clip is closed
        
        return clip_with_new_audio
    except Exception as e:
        console.print(f"[yellow]⚠️  Failed to replace audio: {e}, using original[/yellow]")
        import traceback
        traceback.print_exc()
        return clip


def merge_snippet_clips(snippet_num: int, snippet_info: dict) -> VideoFileClip | None:
    """
    Get the video clip for a snippet.
    For interpolated videos:
    1. Trim interpolated video to snippet duration
    2. Extract audio from original snippet
    3. Replace interpolated video audio with snippet audio
    """
    processed_videos = find_processed_videos(snippet_num)
    snippet_path = get_snippet_video_path(snippet_info)
    
    if processed_videos:
        console.print(f"   [cyan]Snippet {snippet_num}:[/cyan] Using {len(processed_videos)} processed videos")
        
        # Load original snippet to get duration and audio
        snippet_video = None
        snippet_duration = None
        snippet_audio_path = None  # Path to materialized audio file
        
        if snippet_path.exists():
            try:
                snippet_video = VideoFileClip(str(snippet_path))
                snippet_duration = snippet_video.duration
                
                # Materialize audio to temp file so it survives after snippet_video is closed
                if snippet_video.audio is not None:
                    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_audio:
                        snippet_audio_path = temp_audio.name
                    snippet_video.audio.write_audiofile(snippet_audio_path, logger=None)
                
                snippet_video.close()  # Close now since we have the audio file
                snippet_video = None
            except Exception as e:
                console.print(f"      [yellow]⚠️  Could not load snippet: {e}[/yellow]")
                if snippet_video:
                    snippet_video.close()
        
        # Load all processed video clips
        clips = []
        for vid_path in processed_videos:
            try:
                clip = VideoFileClip(str(vid_path))
                original_duration = clip.duration
                
                # Step 1: Trim interpolated video to snippet duration
                if snippet_duration is not None and clip.duration > snippet_duration:
                    clip = clip.subclipped(0, snippet_duration)
                    console.print(f"      [dim]• {vid_path.name} trimmed {original_duration:.2f}s → {clip.duration:.2f}s[/dim]")
                else:
                    console.print(f"      [dim]• {vid_path.name} ({clip.duration:.2f}s)[/dim]")
                
                # Step 2 & 3: Replace audio with snippet audio (trimmed to clip duration)
                if snippet_audio_path is not None:
                    try:
                        # Load audio from materialized file
                        snippet_audio = AudioFileClip(snippet_audio_path)
                        # Trim to clip duration
                        trimmed_audio = snippet_audio.subclipped(0, min(clip.duration, snippet_audio.duration))
                        clip = clip.with_audio(trimmed_audio)
                    except Exception as e:
                        console.print(f"      [yellow]⚠️  Could not replace audio: {e}[/yellow]")
                
                clips.append(clip)
            except Exception as e:
                console.print(f"      [yellow]⚠️  Failed to load {vid_path.name}: {e}[/yellow]")
        
        # Clean up temp audio file after all clips are processed
        # Note: Don't delete yet - clips still reference it. Will be cleaned up after final write.
        
        if not clips:
            console.print(f"   [yellow]⚠️  No valid processed videos, falling back to original[/yellow]")
            if snippet_audio_path:
                Path(snippet_audio_path).unlink(missing_ok=True)
            return None
        
        # Concatenate processed videos
        if len(clips) == 1:
            return clips[0]
        else:
            merged = concatenate_videoclips(clips, method="compose")
            return merged
    else:
        # Use original snippet
        if not snippet_path.exists():
            console.print(f"   [red]❌ Original snippet not found: {snippet_path}[/red]")
            return None
        
        try:
            clip = VideoFileClip(str(snippet_path))
            console.print(f"   [dim]Snippet {snippet_num}:[/dim] Using original ({clip.duration:.2f}s)")
            return clip
        except Exception as e:
            console.print(f"   [red]❌ Failed to load {snippet_path}: {e}[/red]")
            return None


def merge_all_snippets(output_path: Path) -> bool:
    """Merge all snippets into final video."""
    
    # Load snippet info
    if not Path(SNIPPETS_INFO_FILE).exists():
        console.print(f"[red]❌ Snippets info file not found: {SNIPPETS_INFO_FILE}[/red]")
        return False
    
    with open(SNIPPETS_INFO_FILE) as f:
        snippets_info = json.load(f)
    
    console.print(Panel.fit(
        f"[bold cyan]🎬 MERGE BRANDED VIDEO[/bold cyan]\n"
        f"[white]Merging {len(snippets_info)} snippets into final video[/white]",
        border_style="cyan"
    ))
    
    # Load sponsored video to prepend
    sponsored_clip = None
    sponsored_path = Path(SPONSORED_VIDEO)
    if sponsored_path.exists():
        try:
            sponsored_clip = VideoFileClip(str(sponsored_path))
            console.print(f"[green]✓ Loaded sponsored video ({sponsored_clip.duration:.2f}s)[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠️  Failed to load sponsored video: {e}[/yellow]")
    else:
        console.print(f"[yellow]⚠️  Sponsored video not found: {sponsored_path}[/yellow]")
        console.print("[yellow]   Continuing without sponsored video prepend[/yellow]")
    
    # No need to load goku.mp4 - we use snippet audio for interpolated videos
    console.print("[cyan]Will use snippet audio for interpolated videos[/cyan]\n")
    
    # Collect all video clips (start with sponsored video if available)
    all_clips = []
    if sponsored_clip:
        all_clips.append(sponsored_clip)
    processed_count = 0
    original_count = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Loading snippets...", total=len(snippets_info))
        
        # Limit to snippet 57
        MAX_SNIPPET = 57
        
        for snippet_info in snippets_info:
            snippet_num = snippet_info['snippet_number']
            
            # Stop after max snippet
            if snippet_num > MAX_SNIPPET:
                break
                
            progress.update(task, description=f"[cyan]Loading snippet {snippet_num}/{MAX_SNIPPET}...")
            
            clip = merge_snippet_clips(snippet_num, snippet_info)
            
            if clip is not None:
                all_clips.append(clip)
                if find_processed_videos(snippet_num):
                    processed_count += 1
                else:
                    original_count += 1
            
            progress.advance(task)
    
    
    if not all_clips:
        console.print("[red]❌ No valid video clips found![/red]")
        return False
    
    # Summary
    console.print()
    summary_table = Table(title="Merge Summary", show_header=True, header_style="bold")
    summary_table.add_column("Type", style="cyan")
    summary_table.add_column("Count", style="white")
    if sponsored_clip:
        summary_table.add_row("Sponsored video", "1")
    summary_table.add_row("Processed snippets", str(processed_count))
    summary_table.add_row("Original snippets", str(original_count))
    summary_table.add_row("Total clips", str(len(all_clips)))
    console.print(summary_table)
    console.print()
    
    # Concatenate all clips
    console.print("[cyan]⏳ Concatenating all clips...[/cyan]")
    
    # Use all clips directly - audio has been materialized to temp files
    clips_to_use = all_clips
    
    try:
        if len(clips_to_use) == 1:
            final_video = clips_to_use[0]
        else:
            # Use "compose" method for better audio handling when all clips have audio
            final_video = concatenate_videoclips(clips_to_use, method="compose")
        
        # Check if final video has audio
        has_audio = final_video.audio is not None
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        console.print(f"[cyan]⏳ Writing final video to {output_path}...[/cyan]")
        console.print(f"[dim]   This may take several minutes...[/dim]")
        if not has_audio:
            console.print(f"[yellow]   Note: Final video has no audio[/yellow]")
        
        # Write video with or without audio
        if has_audio:
            final_video.write_videofile(
                str(output_path),
                codec='libx264',
                audio_codec='aac',
                logger=None,  # Suppress moviepy's verbose output
            )
        else:
            final_video.write_videofile(
                str(output_path),
                codec='libx264',
                audio=False,  # No audio track
                logger=None,  # Suppress moviepy's verbose output
            )
        
        console.print(f"[green]✅ Final video saved to: {output_path}[/green]")
        console.print(f"[dim]   Duration: {final_video.duration:.2f}s[/dim]")
        
        # Cleanup
        final_video.close()
        for clip in all_clips:
            clip.close()
        if sponsored_clip:
            sponsored_clip.close()
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Error creating final video: {e}[/red]")
        import traceback
        traceback.print_exc()
        
        # Cleanup on error
        for clip in all_clips:
            try:
                clip.close()
            except:
                pass
        if sponsored_clip:
            try:
                sponsored_clip.close()
            except:
                pass
        
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Merge processed videos with original snippets"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output path for final video (default: final_output/branded_video.mp4)"
    )
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        Path(OUTPUT_DIR).mkdir(exist_ok=True)
        output_path = Path(OUTPUT_DIR) / "branded_video.mp4"
    
    success = merge_all_snippets(output_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

