#!/bin/sh
MUSIC=/usr/share/nginx/html/music
OUT=/usr/share/nginx/html/manifest.jsonl
first=1

echo "[" > "$OUT"
for dir in "$MUSIC"/*/; do
  [ -d "$dir" ] || continue
  cat=$(basename "$dir")
  for f in "$dir"*.mp3; do
    [ -e "$f" ] || continue
    name=$(basename "$f")
    id=${name%%.*}
    [ "$first" -eq 1 ] || echo "," >> "$OUT"
    first=0
    printf '  {"filename":"%s","id":"%s","category":"%s","path":"%s/%s"}' \
      "$name" "$id" "$cat" "$cat" "$name" >> "$OUT"
  done
done
printf '\n]\n' >> "$OUT"
echo "Manifest: $(grep -c filename "$OUT") tracks"