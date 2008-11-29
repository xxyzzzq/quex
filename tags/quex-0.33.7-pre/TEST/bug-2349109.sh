#! /usr/bin/env bash
bug=2349109
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug 0.33.5 Line and Column number counts with Set skippers"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simplism
cd $tmp
