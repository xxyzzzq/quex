#! /usr/bin/env bash
bug=3075601
if [[ $1 == "--hwut-info" ]]; then
    echo "otsakiridis: $bug 0.52.1 Pre-Context with Codec utf8;"
    echo "CHOICES: utf8, utf16;"
    exit
fi

tmp=`pwd`
cd $bug/ 
echo "##No output is good output"
if [[ $1 == "utf8" ]]; then
    quex -i simple.qx -o EasyLexer --language C --codec utf8
elif [[ $1 == "utf16" ]]; then
    quex -i simple.qx -o EasyLexer --language C --codec utf16 -b 2
fi

g++ -c EasyLexer.c -I$QUEX_PATH  

# cleansening
rm EasyLexer*

cd $tmp
