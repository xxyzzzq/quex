#! /usr/bin/env bash
bug=2819043
if [[ $1 == "--hwut-info" ]]; then
    echo "wryun: $bug 0.41.2 Infinite recursion error"
    exit
fi

tmp=`pwd`
cd $bug/ 
echo No output is just fine
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple.cpp Simple-token_ids Simplism
cd $tmp
