#! /usr/bin/env bash
bug=2251359
if [[ $1 == "--hwut-info" ]]; then
    echo "marcoantonelli: $bug (feature) Single-character token without name"
    echo "CHOICES: good, 1, 2, 3, 4, 5, 6;"
    exit
fi

tmp=`pwd`
cd $bug/ 
if [[ $1 == "good" ]]; then
    quex -i good.qx -o Simple
    echo "(*) Core Engine"
    awk ' /token_id_str_/ { print; } ' Simple.cpp 
    echo "(*) Token IDs"
    awk ' /QUEX_TKN_/ { print; } ' Simple-token_ids
else
    quex -i error-$1.qx -o Simple
fi

# cleansening
rm -f Simple Simple.cpp Simple-* *.o
cd $tmp
