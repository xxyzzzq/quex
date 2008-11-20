#! /usr/bin/env bash
bug=1948456
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug (feature) Inheritance Info"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simplism
cd $tmp
