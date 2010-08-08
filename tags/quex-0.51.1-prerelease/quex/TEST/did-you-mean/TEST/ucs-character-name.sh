#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "UCS Character Code Names;"
    echo "CHOICES: 1;"
    exit
fi

quex -i ucs-character-name-$1.qx
