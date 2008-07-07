#! /usr/bin/env bash
bug=1892809
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug "
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx --engine Simple --token-queue
g++ -I./ -I$QUEX_PATH Simple.cpp Simple-core-engine.cpp lexer.cpp -o Simplicism
echo "(1)"
./Simplicism example.txt
echo "(2)"
./Simplicism example-2.txt
#
rm Simple.cpp Simple-core-engine.cpp Simple Simple-token_ids Simplicism
cd $tmp
