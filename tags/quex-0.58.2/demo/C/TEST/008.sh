#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/008: Interface to Bison/Yacc (Contributed by Marco Antonelli)"
    echo "CHOICES:  NDEBUG, DEBUG;"
    echo "SAME;"
    exit
fi
cp 008-side-kick.sh side-kick.sh
source core-new.sh 008 $2 $3 $1
