#! /usr/bin/env bash
bug=2799244
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug 0.39.5 attempts to call unimplemented token set() function"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simplism
cd $tmp
