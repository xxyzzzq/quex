#! /usr/bin/env bash
bug=3079986
if [[ $1 == "--hwut-info" ]]; then
    echo "rmanoj-oss: $bug Allow namespace delimiter in --token-prefix for C++"
    exit
fi

tmp=`pwd`
cd $bug/ 

echo "(0) quexify -- no output is good output"
quex -i simple.qx --token-prefix ParserBase::TKN_ --foreign-token-id-file Parserbase.h >& tmp.txt
cat tmp.txt

echo "(1) check out generated sources"
awk ' /TKN_/ { print; }' lexer.cpp >& tmp.txt
cat tmp.txt

echo "(2) compile -- no output is good output"
g++ -I$QUEX_PATH -c lexer.cpp -I. -Wall -Wconversion >& tmp.txt
cat tmp.txt

rm tmp.txt

# cleansening
rm -rf lexer*
rm -rf tmp.txt
cd $tmp
