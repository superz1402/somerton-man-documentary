#!/bin/sh
# Somerton Man documentary — one-command build (clone mode)
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
LIB=${LIB:-$(cd "$HERE/../.." && pwd)}
export LIB
[ -f "$LIB/core/render/video.mjs" ] || { echo "set LIB to the lemo-opuscar library folder"; exit 1; }
cd "$LIB"
node core/render/events.mjs "$HERE"
node core/render/video.mjs "$HERE" --fps 24 --workers 2 --out "$HERE/out/video.mp4"
"$LIB/.venv/bin/python" "$HERE/mix.py"
sh core/render/mux.sh "$HERE/out/video.mp4" "$HERE/out/mix.wav" "$HERE/somerton-man.mp4" 24
"$LIB/.venv/bin/python" core/render/srt.py "$HERE/cues.json" "$HERE/somerton-man.srt"
echo "done: $HERE/somerton-man.mp4"
