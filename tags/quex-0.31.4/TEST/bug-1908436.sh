#! /usr/bin/env bash
bug=1908436
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug 0.23.6 rule precedence reversed for identical patterns"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simplism
cd $tmp
