#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/003: Unicode Based Lexical Analyzis"
    echo "CHOICES:  BPC=2, BPC=2_NDEBUG, BPC=4, BPC=4_NDEBUG, BPC=wchar_t"
    exit
fi

if [[ $1 == "BPC=2_NDEBUG" ]]; then
    args="DNDEBUG BYTES_PER_CHARACTER=2"
fi
if [[ $1 == "BPC=2_DEBUG" ]]; then
    args="BYTES_PER_CHARACTER=2"
fi
if [[ $1 == "BPC=4" ]]; then
    args="BYTES_PER_CHARACTER=4"
fi
if [[ $1 == "BPC=4_NDEBUG" ]]; then
    args="NDEBUG BYTES_PER_CHARACTER=4"
fi
if [[ $1 == "BPC=wchar_t" ]]; then
    args="BYTES_PER_CHARACTER=wchar_t"
fi
source core.sh 003 $args 
