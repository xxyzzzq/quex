#! /usr/bin/env bash
bug=2395200
if [[ $1 == "--hwut-info" ]]; then
    echo "nobody: $bug assert  in QuexBufferFiller_load_forward (The StrangeStream Issue)"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simplism
cd $tmp
