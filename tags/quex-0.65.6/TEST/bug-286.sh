#! /usr/bin/env bash
bug=286
if [[ $1 == "--hwut-info" ]]; then
    echo "attardi: $bug Maintaining character index during manual buffer filling."
    exit
fi

tmp=`pwd`
cd $bug/ 

make clean >& /dev/null
make >& /dev/null

cat example.txt | ./lexer
make clean >& /dev/null

