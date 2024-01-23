#!/usr/bin/env bash

set -euo pipefail

ansible_result=ANSIBLE_FAILED tmux start-server\; run '

sleep 1

source ~/.tmux/plugins/tpm/tpm
source ~/.tmux/plugins/tpm/scripts/helpers/plugin_functions.sh

result=ANSIBLE_OK

for plugin in $(tpm_plugins_list_helper); do
	if ! plugin_already_installed "$plugin"; then
		~/.tmux/plugins/tpm/scripts/install_plugins.sh
		result=ANSIBLE_CHANGED
		break
	fi
done

tmux setenv -g ansible_result "$result"
'\; show-environment -g ansible_result | sed 's/^ansible_result=//'
