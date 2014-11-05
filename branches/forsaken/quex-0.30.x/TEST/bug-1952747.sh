#! /usr/bin/env bash
bug=1952747
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug TKN_TERMINATION"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i simple.qx -o Simple
grep -e user_specified_tkn_termination_handler Simple-core-engine.cpp
# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids 
cd $tmp
