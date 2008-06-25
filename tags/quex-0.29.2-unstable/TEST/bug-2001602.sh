#! /usr/bin/env bash
bug=2001602
if [[ $1 == "--hwut-info" ]]; then
    echo "attardi: $bug RE matching UTF8 l quote uno"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token-ids Simplism
cd $tmp
