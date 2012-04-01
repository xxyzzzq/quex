#! /usr/bin/env bash
bug=3079986
if [[ $1 == "--hwut-info" ]]; then
    echo "rmanoj-oss: $bug Allow namespace delimiter in --token-id-prefix for C++"
    echo "CHOICES: nnn, nnc, ncc, ccc;"
    echo "SAME;"
    exit
fi

tmp=`pwd`
cd $bug/ 

testcase=$1

sed "s/Parserbase-XXX/Parserbase-$testcase/" simple-XXX.qx > simple.qx

echo "(0) quexify -- no output is good output"
quex -i simple.qx --token-id-prefix scope1::scope2::scope3::TKN_ --foreign-token-id-file Parserbase-$testcase.h >& tmp.txt
cat tmp.txt

echo "(1) check out generated sources"
awk ' /TKN_/ { print; }' Lexer.cpp >& tmp.txt
cat tmp.txt

echo "(2) compile -- no output is good output"
g++ -I$QUEX_PATH -c Lexer.cpp -I. -Wall -Wconversion >& tmp.txt
cat tmp.txt

# cleanup
rm -f simple.qx tmp.txt
rm -rf Lexer*
rm -rf tmp.txt

cd $tmp
