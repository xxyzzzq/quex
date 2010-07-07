#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/007: Miscellaneous Features"
    echo "CHOICES:  NDEBUG, DEBUG;"
    echo "SAME;"
    exit
fi
source core-new.sh 007 $2 $3 $1
