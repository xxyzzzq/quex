#! /usr/bin/env bash
bug=1893113
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug PATCH Performance modifications of 0.20.4"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token-ids Simplism
cd $tmp
