# Software for Keeping Carbon Stored was built in Godot 4.6.

## Command prompt line for changing .mov files into the Godot-compatible .ogv (must have ffmpeg installed first):
ffmpeg -i fileToChange.mov -s 1920x1080 -vcodec libtheora -acodec libvorbis newFileName.ogv
