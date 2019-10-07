#!/usr/bin/env bash

set -euo pipefail

temp_file=$(mktemp)
clean_up() {
	rm -f "$temp_file"
}
trap clean_up EXIT
curl -o "$temp_file" https://beta.quicklisp.org/quicklisp.lisp
hash=$(openssl sha256 "$temp_file" | cut -d' ' -f2)
if [ "$hash" != "4a7a5c2aebe0716417047854267397e24a44d0cce096127411e9ce9ccfeb2c17" ]; then
	echo "quicklisp.lisp has unexpected SHA256: $hash" >&2
	exit 1
fi
sbcl --load "$temp_file" --eval '(quicklisp-quickstart:install)'
