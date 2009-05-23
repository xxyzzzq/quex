#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "Miscellaneous Sample Runs"
    echo "CHOICES:  empty, ;"
    echo "SAME;"
    exit
fi

quex -i token_type-$1.qx -o Simple
