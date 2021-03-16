#!/usr/bin/env bash

if [ $# -ne 1 ]; then
	echo "Usage: $(basename "$0") <dest>" >&2
	exit 1
fi

temp_dir=$(mktemp -d)

rm_temp_dir() {
	rm -r "$temp_dir"
}
trap rm_temp_dir EXIT

cd "$temp_dir"
curl -Lo file-icons.woff2 \
     'https://github.com/file-icons/atom/raw/master/fonts/file-icons.woff2'

woff2_decompress file-icons.woff2
mv file-icons.ttf "$1"
