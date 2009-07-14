#! /usr/bin/env bash
bug=2820813
if [[ $1 == "--hwut-info" ]]; then
    echo "prombergerm: $bug 0.41.2 negated character class error"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simplism
cd $tmp
