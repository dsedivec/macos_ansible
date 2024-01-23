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
	# Supposedly important on macOS to get around 1024 file descriptor
	# limit.
	#--with-poll
	--with-xwidgets
	--with-zlib
	--with-xml2
	--with-json
	--with-cairo
	--with-gnutls
	--with-{xpm,jpeg,tiff,gif,png,rsvg}
	--with-tree-sitter
	# Explicitly turn off ImageMagick because sure it's full of holes.
	--without-imagemagick
)

native_comp=0
install_emacs=1

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
			configure_args+=(--with-native-compilation)
			export NATIVE_FULL_AOT=1
			if [ -d /opt/local/etc/macports ]; then
				# MacPorts needs this.  Homebrew Just Works™.
				export LDFLAGS="-Wl,-rpath /opt/local/lib/gcc12"
			fi
			# native-comp author recommends against comp-speed 3.
			#make_args+=('BYTE_COMPILE_EXTRA_FLAGS=--eval "(setq comp-speed 3)"')
			shift 1
			;;

		--no-install)
			install_emacs=0
			shift 1
			;;

		*)
			echo "Usage: $(basename "$0") [--debug-build] [--native-comp] [--no-install]" >&2
			exit 1
			;;
	esac
done

# Always make sure MacPorts is on my PATH before Homebrew, so its
# pkg-config, etc. get picked up in preferfer to Homebrew's.
if [ -d /opt/local/etc/macports ]; then
	PATH=/opt/local/bin:/opt/local/sbin:$PATH
fi

export CC="ccache clang"

# Too many open files?  You need the better select!
# Courtesy https://gitlab.kitware.com/utils/kwsys/-/merge_requests/249/diffs
# and more other bugs than I can possibly imagine.
#
# God I need to switch to Linux.
#
# Note: 10240 comes from grepping for OPEN_MAX in system headers.
CFLAGS="${CFLAGS:-} -D_DARWIN_UNLIMITED_SELECT=1 -DFD_SETSIZE=10240"
export CFLAGS

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

new_emacs=$build_dir/Emacs.app

if [ $native_comp -eq 1 ]; then
	emacs_version=$(perl -ne '
		if (/^#define\s+PACKAGE_VERSION\s+"([^"]+)"/) { print "$1\n"; exit }
	' src/config.h)
	ln -s "MacOS/lib/emacs/${emacs_version}/native-lisp" "$new_emacs/Contents/"
fi

if [ $install_emacs -eq 1 ]; then
	install -d ~/Applications
	dest=$HOME/Applications/Emacs.app
	if [ -e "$dest" ]; then
		old=$HOME/Applications/Emacs\ Old.app
		rm -rf "$old"
		mv "$dest" "$old"
	fi
	mv "$new_emacs" "$dest"
fi
