#! /usr/bin/env bash
#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/004: A C-Lexical Analyser;"
    echo "CHOICES:  NDEBUG, DEBUG;"
    echo "SAME;"
    exit
fi
source core.sh 004 $1

