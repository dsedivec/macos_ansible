#!/usr/bin/env bash

set -euo pipefail

if [ $# -lt 2 ] || [ $# -gt 3 ]; then
	echo "Usage: $(basename "$0") <url> <glob> [<dest dir>]" >&2
	exit 1
fi
url=$1
font_glob=$2
dest_dir=${3:-$HOME/Library/Fonts}

temp_dir=$(mktemp -d)

clean_up_temp_dir() {
	rm -r "$temp_dir"
}

trap clean_up_temp_dir EXIT

cd "$temp_dir"
curl -o fonts.zip "$url"
unzip fonts.zip
if [ ! -d "$dest_dir" ]; then
	mkdir -p "$dest_dir"
fi
find "$temp_dir" -name "$font_glob" -print0 |
	xargs -0 -J % mv -v % "$dest_dir"
