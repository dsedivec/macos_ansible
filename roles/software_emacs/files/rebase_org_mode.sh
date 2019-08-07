#!/usr/bin/env bash

set -euo pipefail

UPSTREAM_REMOTE=upstream
UPSTREAM_BRANCH=master
UPSTREAM_URL=https://code.orgmode.org/bzg/org-mode.git

if remote_url=$(git config remote."$UPSTREAM_REMOTE".url); then
	if [ "$remote_url" != "$UPSTREAM_URL" ]; then
		git remote set-url "$UPSTREAM_REMOTE" "$UPSTREAM_URL"
	fi
else
	git remote add "$UPSTREAM_REMOTE" "$UPSTREAM_URL"
fi

git fetch "$UPSTREAM_REMOTE"
before=$(git rev-parse HEAD)
git rebase "$UPSTREAM_REMOTE/$UPSTREAM_BRANCH"
if [ "$before" != "$(git rev-parse HEAD)" ]; then
	exit 111
else
	exit 0
fi
