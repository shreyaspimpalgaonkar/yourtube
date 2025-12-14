#!/usr/bin/env python3
# Quick fix script to correct indentation
with open('merge_branded_video.py', 'r') as f:
    lines = f.readlines()

# Fix line 533 (index 532)
if len(lines) > 532:
    # Line 533 should be indented properly inside the try block
    # It currently has 16 spaces, needs 20 spaces (4 more)
    line_533 = lines[532]
    if line_533.strip().startswith('_ = clip.audio.duration'):
        # Replace with properly indented version
        lines[532] = '                    _ = clip.audio.duration\n'

with open('merge_branded_video.py', 'w') as f:
    f.writelines(lines)

print("Fixed indentation")

