#! /usr/bin/env bash
bug=2001602
if [[ $1 == "--hwut-info" ]]; then
    echo "attardi: $bug RE matching UTF8 l quote uno"
    exit
fi

tmp=`pwd`
cd $bug/ 
make
./a.out test.utf8
make clean
cd $tmp
