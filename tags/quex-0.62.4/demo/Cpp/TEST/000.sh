#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/000: Single Mode Example"
    echo "CHOICES:  NDEBUG, DEBUG;"
    echo "SAME;"
    exit
fi
source core-new.sh 000 $2 $3 $1
