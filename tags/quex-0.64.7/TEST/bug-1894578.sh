#! /usr/bin/env bash
bug=1894578
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug header block not added to -core-engine.cpp file in 0.20.6"
    exit
fi

tmp=`pwd`
cd $bug/ 
echo "If no errors occur in compilation, then everything is fine"
quex -i error.qx -o Simple
rm -f Simlicism
g++ -I./ -I$QUEX_PATH Simple.cpp  ../lexer-simply.cpp my_function.cpp -o Simlicism -Wall
ls Simlicism

rm -f Simple Simple.cpp Simple-* Simlicism
cd $tmp
