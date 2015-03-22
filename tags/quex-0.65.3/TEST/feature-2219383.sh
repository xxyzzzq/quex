#! /usr/bin/env bash
bug=2219383
if [[ $1 == "--hwut-info" ]]; then
    echo "marcoantonelli: $bug Parse foreign token id file"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i simple.qx -o Simple --token-id-prefix TKN_ --foreign-token-id-file Calc_token-ids.h --foreign-token-id-file-show

# cleansening
rm -f Simple Simple.cpp Simple-* *.o tmp.txt
cd $tmp
