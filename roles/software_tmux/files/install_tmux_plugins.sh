#!/usr/bin/env bash

tmux start-server\; run '

source ~/.tmux/plugins/tpm/tpm
source ~/.tmux/plugins/tpm/scripts/helpers/plugin_functions.sh

for plugin in $(tpm_plugins_list_helper); do
	if ! plugin_already_installed "$plugin"; then
		~/.tmux/plugins/tpm/scripts/install_plugins.sh
		echo "ANSIBLE_CHANGED"
		break
	fi
done

echo "ANSIBLE_OK"
'
