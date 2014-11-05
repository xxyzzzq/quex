#! /usr/bin/env bash
bug=1893880
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug 0.20.5 allows inheritable: only start mode"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simplism
cd $tmp
