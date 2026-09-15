# Software for Keeping Carbon Stored was built in Godot 4.6.

## Command prompt line for changing .mov files into the Godot-compatible .ogv keeping the same file size (must have ffmpeg installed first):
ffmpeg -i input.mov -q:v 6 -q:a 6 -g:v 64 output.ogv

## Command prompt line for keeping quality and resizing to 1920x1080:
ffmpeg -i input.ogv -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" -c:v libtheora -q:v 7 -c:a copy output.ogv

[This Godot doc](https://docs.godotengine.org/en/latest/tutorials/animation/playing_videos.html) also talks about ffmpeg and how to use.
