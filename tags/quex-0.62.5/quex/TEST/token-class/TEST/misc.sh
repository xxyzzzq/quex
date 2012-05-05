#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "Miscellaneous Sample Runs"
    echo "CHOICES:  empty, no-namespace, double-colon, token;"
    exit
fi

quex -i token_type-$1.qx -o Simple

if [[ $1 == "no-namespace" ]]; then
    grep -e QToken Simple-token
    rm -f Simple*
fi
