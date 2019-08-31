#!/usr/bin/env bash

set -euo pipefail

extra_config=''

if [[ $# -eq 1 && "$1" = "debug" ]]; then
	# See etc/DEBUG in Emacs sources.
	echo "building with debugging options"
	export CFLAGS='-O0 -g3'
	extra_config="--enable-checking=yes,glyphs
	              --enable-check-lisp-object-type"
elif [[ $# -ne 0 ]]; then
	echo "usage: $(basename "$0") [debug]" >&2
	exit 1
fi

export CC="ccache gcc"
num_procs=$(getconf _NPROCESSORS_ONLN)
export MAKEFLAGS=-j$num_procs

if [ ! -f src/emacs.c ]; then
	echo "Can't find src/emacs.c, wrong PWD?" 2>&1
	exit 1
fi

git clean -Xdf
./autogen.sh
./configure --with-ns --without-x --with-modules \
            --with-xml2 --with-json --with-cairo --with-gnutls \
            --with-{xpm,jpeg,tiff,gif,png,rsvg} \
            $extra_config
# Must "make" before "make install", otherwise you don't get man and
# info installed in the app bundle.
make
make install
install -d ~/Applications
dest=$HOME/Applications/Emacs.app
if [ -e "$dest" ]; then
	old=$HOME/Applications/Emacs\ Old.app
	rm -rf "$old"
	mv "$dest" "$old"
fi
mv nextstep/Emacs.app "$dest"
