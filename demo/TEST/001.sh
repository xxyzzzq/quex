#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/001: Multiple Modes, Mode Transitions"
    echo "CHOICES:  NDEBUG, DEBUG;"
    echo "SAME;"
    exit
fi
source core.sh 001 $1
