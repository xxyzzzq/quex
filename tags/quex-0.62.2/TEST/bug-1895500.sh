#! /usr/bin/env bash
bug=1895500
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug assertion error running generated 0.20.8 lexer with Unicode"
    echo "CHOICES: iconv, icu;"
    echo "SAME;"
    exit
fi

tmp=`pwd`
cd $bug/ 

if [[ $2 == "FIRST" ]]; then
    make clean
fi

make lexer-$1
./lexer-$1 example-utf-8.dat

# cleansening
if [[ $3 == "LAST" ]]; then
   make clean
fi

cd $tmp
