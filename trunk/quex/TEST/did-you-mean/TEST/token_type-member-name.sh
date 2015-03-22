#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "Explicit Token Type Member Assignment;"
    exit
fi

quex -i token_type-member-name.qx --suppress 15 # --debug-exception
