#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/003: Unicode Based Lexical Analyzis"
    echo "CHOICES:  BYTES_PER_CHARACTER=2, BYTES_PER_CHARACTER=4, BYTES_PER_CHARACTER=whar_t"
    exit
fi
source core.sh $1 003
