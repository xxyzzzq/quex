#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "Source Packager: C;"
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
        option='-i example_token-c.qx simple.qx'
        ;;
    manual-token-class)
        option='-i simple.qx --token-class-file example_token.h --token-class blackray::token'
        ;;
esac

if [ -d pkg ]; then
    rm -rf pkg/*
else
    mkdir pkg
fi


echo "(0) Running Quex (no output is good output)"
quex -o EasyLexer --source-package pkg $option --language C

echo "(1) Running gcc (no output is good output)"
gcc  -Ipkg -I. pkg/EasyLexer.c -o pkg/EasyLexer.o -c -Wall -W

echo "(2) Double check that output file exists"
ls    pkg/EasyLexer.o

