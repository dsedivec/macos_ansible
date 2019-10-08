#!/usr/bin/env bash

set -euo pipefail

URL=https://raw.githubusercontent.com/borkdude/clj-kondo/master/script/install-clj-kondo

[ $# -eq 1 ] || exit 1

bash <(curl -s "$URL") --dir "$1"
clj_kondo=$1/clj-kondo
[ -x "$clj_kondo" ] || exit 1
# Weirdly, the binary comes out being group "wheel"?
chgrp $(id -g) "$clj_kondo"
