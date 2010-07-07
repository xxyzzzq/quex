#! /usr/bin/env bash
#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/004: A C-Lexical Analyser;"
    echo "CHOICES:  NDEBUG, DEBUG;"
    echo "SAME;"
    exit
fi
cp 004-side-kick.sh side-kick.sh
source core-new.sh 004 $2 $3 $1

