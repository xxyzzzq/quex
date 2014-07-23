#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/012b: Multiple Lexical Analyzers -- shared token"
    echo "CHOICES:  NDEBUG, DEBUG;"
    echo "SAME;"
    exit
fi
cp 012-side-kick.sh side-kick.sh
source core-new.sh 012b $2 $3 $1
