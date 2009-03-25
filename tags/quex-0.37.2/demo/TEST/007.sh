#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/007: Miscellaneous Features"
    echo "CHOICES:  NDEBUG, DEBUG;"
    echo "SAME;"
    exit
fi
source core.sh 007 $1
