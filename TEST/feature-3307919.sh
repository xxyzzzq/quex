#! /usr/bin/env bash
bug=3307919
if [[ $1 == "--hwut-info" ]]; then
    echo "jmarsik: $bug Support for more general Unicode categories;"
    echo "CHOICES: C, Other, L, LC, M, N, Number, P, S, Z;"
    exit
fi
quex --set-by-expression "\G{$1}" # --debug-exception
