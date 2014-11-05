#! /usr/bin/env bash
bug=2004927
if [[ $1 == "--hwut-info" ]]; then
    echo "attardi: $bug UTF-8 RE Extra Comma Matched"
    exit
fi

tmp=`pwd`
cd $bug/ 
make
./a.out example.dat
make clean
cd $tmp
