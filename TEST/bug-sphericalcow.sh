#! /usr/bin/env bash
bug=sphericalcow
if [[ $1 == "--hwut-info" ]]; then
    echo "2798423: $bug 0.39.4 token_type default __copy function doesnt"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simplism
cd $tmp
