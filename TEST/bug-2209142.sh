#! /usr/bin/env bash
bug=2209142
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug 0.33.1-pre-release: RE not suited for comment elimination;"
    echo "CHOICES: error, good;"
    exit
fi

tmp=`pwd`
cd $bug/ 
make $1
./$1
make clean
cd $tmp
