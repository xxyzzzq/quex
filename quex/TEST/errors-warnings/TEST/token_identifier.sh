#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "Token identifier definition and orthography.;"
    exit
fi

quex -i qx/token-id.qx -o Simple # --debug-exception
rm -f Simple*
