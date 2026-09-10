#!/bin/sh
printf '\033c\033]0;%s\a' Climate Action Venn Diagram
base_path="$(dirname "$(realpath "$0")")"
"$base_path/Venn_Diagram.x86_64" "$@"
