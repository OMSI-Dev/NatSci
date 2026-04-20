# Software for Keeping Carbon Stored was built in Godot 4.6.

## Command prompt line for changing .mov files into the Godot-compatible .ogv (must have ffmpeg installed first):
ffmpeg -i input.mov -q:v 6 -q:a 6 -g:v 64 output.ogv

[This Godot doc](https://docs.godotengine.org/en/latest/tutorials/animation/playing_videos.html) also talks about ffmpeg and how to use.
