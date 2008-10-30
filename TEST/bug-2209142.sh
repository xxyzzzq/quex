#! /usr/bin/env bash
bug=2209142
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug 0.33.1-pre-release: RE not suited for comment elimination"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simplism
cd $tmp
