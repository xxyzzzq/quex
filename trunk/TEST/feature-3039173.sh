#! /usr/bin/env bash
bug=3039173
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug On Mismatch: abort()"
    exit
fi

tmp=`pwd`
cd $bug/ 

quex -i simple.qx -o Simple
g++ ../lexer.cpp Simple.cpp -I. -I$QUEX_PATH -o lexer
./lexer example.txt 
rm -f Simple* 
rm -f lexer

# cleansening
cd $tmp
