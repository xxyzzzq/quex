#! /usr/bin/env bash
bug=1895500
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug assertion error running generated 0.20.8 lexer with Unicode"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token-ids Simplism
cd $tmp
