#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "Source Packager: C++;"
    echo "CHOICES: plain, iconv, icu, codec, codec-utf8, codec-utf16, post-categorizer, no-string-accumulator, no-include-stack, no-counter;"
    echo "SAME;"
    exit
fi


case $1 in
    plain) 
        option=''
        ;;
    iconv)
        option='--iconv'
        ;;
    icu)
        option='--icu'
        ;;
    codec)
        option='--codec iso8859_7'
        ;;
    codec-utf8)
        option='--codec utf8'
        ;;
    codec-utf16)
        option='--codec utf16 --bes 2'
        ;;
    post-categorizer)
        option='--icu --post-categorizer'
        ;;
    no-string-accumulator)
        option='--no-string-accumulator'
        ;;
    no-include-stack)
        option='--icu --no-include-stack'
        ;;
    no-counter)
        option='--no-count-lines --no-count-columns'
        ;;
esac

rm -rf pkg/*

echo "(0) Running Quex (no output is good output)"
quex -i simple.qx -o EasyLexer --source-package pkg $option

echo "(1) Running g++ (no output is good output)"
g++  -Ipkg -I. pkg/EasyLexer.cpp -o pkg/EasyLexer.o -c -Wall -W

echo "(2) Double check that output file exists"
ls    pkg/EasyLexer.o

