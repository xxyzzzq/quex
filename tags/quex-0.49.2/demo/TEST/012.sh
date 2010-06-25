#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/012: Single Application/Multiple Lexical Analyzers"
    echo "CHOICES:  NDEBUG, DEBUG;"
    echo "SAME;"
    exit
fi
source core.sh 012 $1
