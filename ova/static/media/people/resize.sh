#!/usr/bin/env bash

# Resize & compress images from /original/ to /small/ using ffmpeg

INPUT_DIR="$(dirname "$0")/original"
OUTPUT_DIR="$(dirname "$0")/small"

mkdir -p "$OUTPUT_DIR"

for file in "$INPUT_DIR"/*.{jpg,jpeg,png,JPG,JPEG,PNG}; do
    [ -e "$file" ] || continue

    filename=$(basename "$file")
    name="${filename%.*}"
    output="$OUTPUT_DIR/$name.jpg"

    # Skip if already processed
    if [ -f "$output" ]; then
        echo "Skipping $filename"
        continue
    fi

    echo "Processing $filename → $output"

    # Resize so smaller side is 480px, keeping aspect ratio
    ffmpeg -i "$file" \
        -vf "scale='if(gt(iw,ih),-1,480)':'if(gt(ih,iw),-1,480)'" \
        -q:v 3 \
        -y "$output"
done