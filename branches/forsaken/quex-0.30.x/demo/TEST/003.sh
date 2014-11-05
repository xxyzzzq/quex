#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/003: Unicode Based Lexical Analyzis"
    echo "CHOICES:  BPC=2, BPC=2_NDEBUG, BPC=4, BPC=4_NDEBUG, BPC=wchar_t;"
    echo "SAME;"
    exit
fi

case $1 in
"BPC=2" )        args="BYTES_PER_CHARACTER=2" ;;
"BPC=2_NDEBUG" ) args="NDEBUG BYTES_PER_CHARACTER=2" ;;
"BPC=4" )        args="BYTES_PER_CHARACTER=4" ;;
"BPC=4_NDEBUG" ) args="NDEBUG BYTES_PER_CHARACTER=4" ;;
"BPC=wchar_t" )  args="BYTES_PER_CHARACTER=wchar_t" ;;
esac

source core.sh 003 $args ## 
