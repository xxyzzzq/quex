#! /usr/bin/env bash
bug=1895500
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug assertion error running generated 0.20.8 lexer with Unicode"
    exit
fi

tmp=`pwd`
cd $bug/ 
make
./a.out
# cleansening
make clean

cd $tmp
