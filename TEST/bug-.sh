#! /usr/bin/env bash
bug=
if [[ $1 == "--hwut-info" ]]; then
    echo ": $bug "
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simplism
cd $tmp
