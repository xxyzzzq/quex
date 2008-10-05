#! /usr/bin/env bash
bug=2146712
if [[ $1 == "--hwut-info" ]]; then
    echo "yaroslav_xp: $bug output directory parameter for the command line"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simplism
cd $tmp
