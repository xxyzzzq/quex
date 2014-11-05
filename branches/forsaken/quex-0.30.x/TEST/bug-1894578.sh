#! /usr/bin/env bash
bug=1894578
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug header block not added to -core-engine.cpp file in 0.20.6"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple
g++ -I./ -I$QUEX_PATH Simple.cpp Simple-core-engine.cpp lexer.cpp -o Simlicism
cd $tmp
