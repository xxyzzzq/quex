#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/008: Interface to Bison/Yacc (Contributed by Marco Antonelli)"
    echo "CHOICES:  NDEBUG, DEBUG;"
    echo "SAME;"
    exit
fi
export no_valgrind=YES
source core.sh 008 $1
