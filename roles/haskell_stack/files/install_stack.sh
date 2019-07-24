#!/usr/bin/env bash

set -euo pipefail

GITHUB_URL=https://api.github.com/repos/commercialhaskell/stack/releases/latest
JQ_SCRIPT='
.assets
| map(
    select(
        .name
        | test("^stack-[\\d.]+-osx-x86_64.tar.gz$")
    )
)
[0]
.browser_download_url
'

if [ $# != 1 ]; then
	echo "usage: $(basename "$0") <dest dir>" >&2
	exit 1
fi
dest_dir=$1

temp_dir=$(mktemp -d)
[ -n "$temp_dir" ]
clean_temp_dir() {
	rm -r "$temp_dir"
}
trap clean_temp_dir EXIT
cd "$temp_dir"

tarball_url=$(curl "$GITHUB_URL" | jq -r "$JQ_SCRIPT")
curl -Lo stack.tgz "$tarball_url"
tar -xf stack.tgz
cp stack-*-osx-x86_64/stack "$dest_dir/stack"
