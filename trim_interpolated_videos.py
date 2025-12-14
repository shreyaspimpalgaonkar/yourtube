#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = ["moviepy>=2.0", "rich"]
# ///
"""
Trim interpolated videos to match snippet durations and save as _trimmed.mp4 files.

For each interpolated video in interpolated/{snippet_num}/:
- If snippet duration < 8 seconds, trim the video to snippet duration
- Save as {original_name}_trimmed.mp4
- This ensures audio continuity during merging
"""

import json
from pathlib import Path
from moviepy import VideoFileClip

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.panel import Panel

console = Console()

INTERPOLATED_DIR = "interpolated"
SNIPPETS_INFO = "snippets/snippets_info.json"


def load_snippets_info() -> dict:
    """Load snippets info and return as dict keyed by snippet_number."""
    if not Path(SNIPPETS_INFO).exists():
        console.print(f"[red]❌ {SNIPPETS_INFO} not found![/red]")
        return {}
    
    with open(SNIPPETS_INFO) as f:
        snippets = json.load(f)
    
    return {s['snippet_number']: s for s in snippets}


def find_all_interpolated_videos() -> list[tuple[int, Path]]:
    """Find all interpolated videos, returning (snippet_num, video_path) tuples."""
    interpolated_path = Path(INTERPOLATED_DIR)
    
    if not interpolated_path.exists():
        return []
    
    videos = []
    for snippet_dir in sorted(interpolated_path.iterdir()):
        if snippet_dir.is_dir():
            try:
                snippet_num = int(snippet_dir.name)
            except ValueError:
                continue
            
            for video_file in snippet_dir.glob("*.mp4"):
                # Skip already trimmed files
                if "_trimmed.mp4" in video_file.name:
                    continue
                videos.append((snippet_num, video_file))
    
    return videos


def trim_interpolated_video(video_path: Path, snippet_info: dict) -> Path | None:
    """Trim interpolated video to snippet duration if needed. Returns path to trimmed file."""
    snippet_duration = snippet_info.get('duration', 0)
    
    if snippet_duration <= 0:
        return None
    
    try:
        video = VideoFileClip(str(video_path))
        video_duration = video.duration
        
        # Only trim if snippet is shorter than video
        if snippet_duration >= video_duration:
            video.close()
            return None
        
        # Create trimmed filename
        trimmed_path = video_path.parent / f"{video_path.stem}_trimmed.mp4"
        
        # Skip if already exists
        if trimmed_path.exists():
            video.close()
            return trimmed_path
        
        # Trim the video
        trimmed_video = video.subclipped(0, snippet_duration)
        
        # Write trimmed video
        trimmed_video.write_videofile(
            str(trimmed_path),
            codec='libx264',
            audio_codec='aac',
            logger=None
        )
        
        # Cleanup
        trimmed_video.close()
        video.close()
        
        return trimmed_path
    except Exception as e:
        console.print(f"   [red]❌ Error trimming {video_path.name}: {e}[/red]")
        return None


def main():
    console.print(Panel.fit(
        "[bold cyan]✂️  TRIM INTERPOLATED VIDEOS[/bold cyan]\n"
        "[white]Trimming interpolated videos to match snippet durations[/white]",
        border_style="cyan"
    ))
    
    # Load snippets info
    console.print(f"\n[cyan]Loading snippets info...[/cyan]")
    snippets_info = load_snippets_info()
    
    if not snippets_info:
        console.print("[red]❌ Cannot proceed without snippets info[/red]")
        return
    
    console.print(f"[green]✓ Loaded {len(snippets_info)} snippets[/green]\n")
    
    # Find all interpolated videos
    console.print("[cyan]Finding interpolated videos...[/cyan]")
    videos = find_all_interpolated_videos()
    
    if not videos:
        console.print("[yellow]⚠️  No interpolated videos found[/yellow]")
        return
    
    console.print(f"[green]✓ Found {len(videos)} video(s)[/green]\n")
    
    # Process each video
    trimmed_count = 0
    skipped_count = 0
    error_count = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Trimming videos...", total=len(videos))
        
        for snippet_num, video_path in videos:
            snippet_info = snippets_info.get(snippet_num)
            if not snippet_info:
                progress.update(task, description=f"[yellow]Snippet {snippet_num} not found in info, skipping...[/yellow]")
                skipped_count += 1
                progress.advance(task)
                continue
            
            progress.update(task, description=f"[cyan]Processing {video_path.name}...[/cyan]")
            
            result = trim_interpolated_video(video_path, snippet_info)
            
            if result:
                trimmed_count += 1
                snippet_duration = snippet_info.get('duration', 0)
                console.print(f"   [green]✓[/green] {video_path.name} → {result.name} ({snippet_duration:.2f}s)")
            elif result is None and snippet_info.get('duration', 0) >= 8:
                # Video doesn't need trimming (snippet >= 8s)
                skipped_count += 1
            else:
                error_count += 1
            
            progress.advance(task)
    
    # Summary
    console.print()
    console.print(f"[green]✅ Successfully trimmed: {trimmed_count}[/green]")
    if skipped_count > 0:
        console.print(f"[yellow]⏭️  Skipped (no trimming needed): {skipped_count}[/yellow]")
    if error_count > 0:
        console.print(f"[red]❌ Errors: {error_count}[/red]")
    console.print()


if __name__ == "__main__":
    main()

