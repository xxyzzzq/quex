#! /usr/bin/env bash
bug=1952747
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug TKN_TERMINATION"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i simple.qx -o Simple
grep -e user_specified_tkn_termination_handler Simple.cpp
# cleansening
rm -f Simple Simple.cpp Simple-*
cd $tmp
