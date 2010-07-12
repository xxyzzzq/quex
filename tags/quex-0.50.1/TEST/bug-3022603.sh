#! /usr/bin/env bash
bug=3022603
if [[ $1 == "--hwut-info" ]]; then
    echo "alexeevm: $bug 0.49.2 Using external buffer with Quex lexer"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i simple.qx -o Simple
g++  point.cpp Simple.cpp -I. -I$QUEX_PATH
./a.out

# cleansening
rm ./a.out Simple*
cd $tmp
