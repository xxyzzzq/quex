#! /usr/bin/env bash
bug=1969629
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug 0.25.4 token list with just TERMINATION treated empty"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple.cpp Simple-token_ids Simplism Simple-configuration
cd $tmp
