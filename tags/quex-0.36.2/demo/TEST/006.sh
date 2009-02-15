#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/006: Pseudo Ambiguous Post Conditions"
    echo "CHOICES:  NDEBUG, DEBUG"
    exit
fi
source core.sh 006 $1
