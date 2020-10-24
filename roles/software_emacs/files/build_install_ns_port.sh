#!/usr/bin/env bash

set -euo pipefail

set_cflags() {
	if [ -n "${CFLAGS:-}" ]; then
		echo "error: CFLAGS already set, I won't override it" >&2
		exit 1
	fi
	export CFLAGS="$*"
}

configure_args=(
	--without-x
	--with-modules
	--with-threads
	--with-xwidgets
	--with-zlib
	--with-xml2
	--with-json
	--with-cairo
	--with-gnutls
	--with-{xpm,jpeg,tiff,gif,png,rsvg}
)

native_comp=0

make_args=("-j$(getconf _NPROCESSORS_ONLN)")

while [ $# -gt 0 ]; do
	case "$1" in
		--debug-build)
			configure_args+=(
				"--enable-checking=yes,glyphs"
				--enable-check-lisp-object-type
			)
			set_cflags '-O0 -g3'
			shift 1
			;;

		--native-comp|--native)
			native_comp=1
			configure_args+=(--with-nativecomp)
			set_cflags '-O2 -I/opt/local/include/gcc10'
			export LDFLAGS=-L/opt/local/lib/gcc10
			# Leaving this on breaks the build:
			#
			#      ELC+ELN   progmodes/js.elc
			#     Symbol’s function definition is void: cc-bytecomp-is-compiling
			#     make[2]: *** [progmodes/js.elc] Error 255
			#     make[1]: *** [compile-main] Error 2
			#     make: *** [lisp] Error 2
			#
			#export NATIVE_FULL_AOT=1
			# native-comp author recommends against comp-speed 3.
			#make_args+=('BYTE_COMPILE_EXTRA_FLAGS=--eval "(setq comp-speed 3)"')
			shift 1
			;;

		*)
			echo "Usage: $(basename "$0") [--debug-build] [--native-comp]" >&2
			exit 1
			;;
	esac
done

export CC="ccache clang"

if [ ! -f src/emacs.c ]; then
	echo "Can't find src/emacs.c, wrong PWD?" 2>&1
	exit 1
fi

git clean -Xdf
# 2020-10-20: Seems this is not yet in .gitignore?  Or it's an error
# that it exists at all?
if [ -d native-lisp ]; then rm -rf native-lisp; fi

./autogen.sh

if ./configure --help | grep -q -- --with-mac; then
	# Unofficial Mac port
	build_dir=$PWD/build
	app_contents=$build_dir/Emacs.app/Contents
	app_res_dir=$app_contents/Resources
	configure_args+=(--with-mac
	                "--enable-mac-app=$build_dir"
	                "--prefix=$app_res_dir"
	                "--exec-prefix=$app_contents/MacOS")
else
	# NS port
	build_dir=$PWD/nextstep
	configure_args+=(--with-ns --enable-ns-self-contained)
fi

./configure "${configure_args[@]}"

# Must "make" before "make install", otherwise you don't get man and
# info installed in the app bundle.
make "${make_args[@]}"
make install
install -d ~/Applications
dest=$HOME/Applications/Emacs.app
if [ -e "$dest" ]; then
	old=$HOME/Applications/Emacs\ Old.app
	rm -rf "$old"
	mv "$dest" "$old"
fi
mv "$build_dir/Emacs.app" "$dest"

if [ $native_comp -eq 1 ]; then
	emacs_version=$(perl -ne '
		if (/^#define\s+PACKAGE_VERSION\s+"([^"]+)"/) { print "$1\n"; exit }
	' src/config.h)
	ln -s "MacOS/lib/emacs/${emacs_version}/native-lisp" "$dest/Contents/"
fi
