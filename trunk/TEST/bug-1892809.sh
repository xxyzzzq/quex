#! /usr/bin/env bash
bug=1892809
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug 0.20.4 \\x, \\X, \\U accept too many digits"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx --engine Simple 
g++ -I./ -I$QUEX_PATH Simple.cpp lexer.cpp -o Simplicism
echo "(1)"
./Simplicism example.txt
echo "(2)"
./Simplicism example-2.txt
#
rm -f Simple Simple.cpp Simple-* Simplicism
cd $tmp
