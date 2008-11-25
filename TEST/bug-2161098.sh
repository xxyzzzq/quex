#! /usr/bin/env bash
bug=2161098
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug 0.32.1 Range Skipper Line Number Counter"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simplism
cd $tmp
