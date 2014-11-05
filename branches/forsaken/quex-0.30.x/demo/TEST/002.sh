#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/002: Indentation Based Scopes"
    echo "CHOICES:  NDEBUG, DEBUG;"
    echo "SAME;"
    exit
fi
source core.sh 002 $1
