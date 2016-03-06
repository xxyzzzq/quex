#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/006: Pseudo Ambiguous Post Conditions"
    echo "CHOICES:  NDEBUG, DEBUG;"
    echo "SAME;"
    exit
fi
cp 006-side-kick.sh side-kick.sh
source core-new.sh 006 $2 $3 $1
