#!/usr/bin/env bash

set -euo pipefail

ROOT=$HOME/.hammerspoon/lua
LUA_VERSION=5.4.0
LUA_SRC_SHA256=eac0836eb7219e421a96b7ee3692b93f0629e4cdb0c788432e3d10ce9ed47e28

SRC_DIR=$ROOT/src

install_lua() {
	install -d "$ROOT/src"
	cd "$SRC_DIR"
	local lua_src_dir=lua-$LUA_VERSION
	local lua_tarball=$lua_src_dir.tar.gz
	local lua_tarball_hash=
	if [ -e "$lua_tarball" ]; then
		lua_tarball_hash=$(openssl sha256 -r "$lua_tarball")
		lua_tarball_hash=${lua_tarball_hash%% *}
	fi
	if [ "$lua_tarball_hash" != "$LUA_SRC_SHA256" ]; then
		rm -f "$lua_tarball"
		curl -O "https://www.lua.org/ftp/$lua_tarball"
	fi
	rm -rf "$lua_src_dir"
	tar -zxf "$lua_tarball"
	cd "$lua_src_dir"
	local normed_root=$ROOT
	if [[ $normed_root =~ (.*?)/+ ]]; then
		normed_root=${BASH_REMATCH[1]}
	fi
	root=$normed_root perl -pi -e \
	     's,#\s*define\s+LUA_ROOT\s+".*?"[ \t]*$,#define LUA_ROOT "${ENV{"root"}}/",' \
	     src/luaconf.h
	make "INSTALL_TOP=$ROOT" all install
}

# Install LuaSocket.
install_luasocket() {
	local lua_socket_repo=$SRC_DIR/luasocket
	local existing_repo=1
	if [ ! -d "$lua_socket_repo" ]; then
		existing_repo=0
		cd "$SRC_DIR"
		git clone https://github.com/diegonehab/luasocket.git
	fi
	cd "$lua_socket_repo"
	if [ $existing_repo -eq 1 ]; then
		git pull --ff
	fi
	git clean -xdf
	make LUAINC_macosx="$ROOT/include" macosx
	[[ $LUA_VERSION =~ ^[0-9]+\.[0-9]+ ]]
	local lua_major_minor=${BASH_REMATCH[0]}
	make prefix="$ROOT" LUAV="$lua_major_minor" install
}

rm -rf "$ROOT"/{bin,include,lib,man,share}
install_lua
export PATH=$ROOT/bin:$PATH
install_luasocket
