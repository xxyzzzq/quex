#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "Source Packager: C;"
    echo "CHOICES: plain, iconv, icu, codec, codec-utf8, codec-utf16, post-categorizer, no-string-accumulator, no-include-stack, no-counter, manual-token-class, customized-token-class;"
    echo "SAME;"
    exit
fi

## Check that Quex can deal with backslashes
## export QUEX_PATH=`echo $QUEX_PATH | sed -e 's/\\//\\\\/g'`

if [ -d pkg ]; then
    rm -rf pkg/*
else
    mkdir pkg
fi

case $1 in
    plain) 
        option='-i simple.qx '
        ;;
    iconv)
        option='-i simple.qx --iconv -b 2'
        ;;
    icu)
        option='-i simple.qx --icu -b 2'
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
        option='-i simple.qx --icu -b 2 --post-categorizer'
        ;;
    no-string-accumulator)
        option='-i simple.qx --no-string-accumulator'
        ;;
    no-include-stack)
        option='-i simple.qx --icu -b 2 --no-include-stack'
        ;;
    no-counter)
        option='-i simple.qx --no-count-lines --no-count-columns'
        ;;
    customized-token-class)
        option='-i example_token-c.qx simple.qx'
        ;;
    manual-token-class)
        cp example_token-c.h pkg/
        option='-i simple.qx --token-class-file example_token-c.h --token-class Token'
        ;;
esac

echo "(0) Running Quex (no output is good output)"
quex -o EasyLexer --source-package pkg $option --language C --debug-exception

echo "(1) Running gcc (no output is good output)"
gcc  -Ipkg pkg/EasyLexer.c -o pkg/EasyLexer.o -c -Wall -W

echo "(2) Double check that output file exists"
ls    pkg/EasyLexer.o 2> tmp.txt
cat tmp.txt

echo "(2.1) Double check that nothing in current directory. (no output is good output)."
ls    EasyLexer* 2> tmp.txt
cat tmp.txt

rm -f tmp.txt


