#! /usr/bin/env bash
bug=2209142
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug 0.33.1-pre-release: RE not suited for comment elimination;"
    echo "CHOICES: error, good;"
    echo "HAPPY:   Simple.cpp:[0-9]+:;"
    exit
fi

tmp=`pwd`
cd $bug/ 
make $1
./$1 2> tmp.txt
cat tmp.txt
rm -f tmp.txt
make clean
cd $tmp
