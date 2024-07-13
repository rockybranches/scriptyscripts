#!/bin/sh

export DEFAULT_SSCRIPTS_SHELL="${SHELL##*/}"
export SSCRIPTS_SHELL=${SSCRIPTS_SHELL:-$DEFAULT_SSCRIPTS_SHELL}
export _SCRIPTYSCRIPTS_COMPLETE="${SSCRIPTS_SHELL}_source scriptyscripts"

_generate_completion_script() {
    _SCRIPTYSCRIPTS_COMPLETE=${SSCRIPTS_SHELL}_source scriptyscripts >~/.scriptyscripts-completion.${SSCRIPTS_SHELL}
}

_add_scriptyscripts_completion() {
    # install scriptyscripts completion
    _generate_completion_script
    #: add scriptyscripts completion to ~/.extend.${SSCRIPTS_SHELL}rc
    _com_cmd='# scriptyscripts completion\neval "$(_SCRIPTYSCRIPTS_COMPLETE='${SSCRIPTS_SHELL}'_source scriptyscripts)"'
    if [ -f ~/.extend.${SSCRIPTS_SHELL}rc ]; then
        if ! grep -q "$_com_cmd" ~/.extend.${SSCRIPTS_SHELL}rc; then
            echo -e "\n\n$_com_cmd" >>~/.extend.${SSCRIPTS_SHELL}rc
        fi
    fi

    #: add scriptyscripts alias to ~/.aliases.${SSCRIPTS_SHELL}rc
    _alias_cmd='# scriptyscripts\nalias sscripts=scriptyscripts\ncompdef sscripts=scriptyscripts'
    if [ -f ~/.aliases.${SSCRIPTS_SHELL}rc ]; then
        if ! grep -q "$_alias_cmd" ~/.aliases.${SSCRIPTS_SHELL}rc; then
            echo -e "\n\n$_alias_cmd" >>~/.aliases.${SSCRIPTS_SHELL}rc
        fi
    fi
}
