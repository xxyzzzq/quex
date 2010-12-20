#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "Source Packager: C++;"
    echo "CHOICES: plain, iconv, icu, codec, codec-utf8, codec-utf16, post-categorizer, no-string-accumulator, no-include-stack, no-counter, manual-token-class, customized-token-class;"
    echo "SAME;"
    exit
fi


case $1 in
    plain) 
        option='-i simple.qx '
        ;;
    iconv)
        option='-i simple.qx --iconv'
        ;;
    icu)
        option='-i simple.qx --icu'
        ;;
    codec)
        option='-i simple.qx --codec iso8859_7'
        ;;
    codec-utf8)
        option='-i simple.qx --codec utf8'
        ;;
    codec-utf16)
        option='-i simple.qx --codec utf16 --bes 2'
        ;;
    post-categorizer)
        option='-i simple.qx --icu --post-categorizer'
        ;;
    no-string-accumulator)
        option='-i simple.qx --no-string-accumulator'
        ;;
    no-include-stack)
        option='-i simple.qx --icu --no-include-stack'
        ;;
    no-counter)
        option='-i simple.qx --no-count-lines --no-count-columns'
        ;;
    customized-token-class)
        option='-i example_token-cpp.qx simple.qx'
        ;;
    manual-token-class)
        option='-i simple.qx --token-class-file example_token.h --token-class Token'
        ;;
esac

if [ -d pkg ]; then
    rm -rf pkg/*
else
    mkdir pkg
fi

echo "(0) Running Quex (no output is good output)"
quex $option -o EasyLexer --source-package pkg 

echo "(1) Running g++ (no output is good output)"
g++  -Ipkg -I. pkg/EasyLexer.cpp -o pkg/EasyLexer.o -c -Wall -W

echo "(2) Double check that output file exists"
ls    pkg/EasyLexer.o

