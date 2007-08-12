#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/000: Single Mode Example"
    echo "CHOICES:  QuexCore"
    exit
fi
source core.sh $1 000
