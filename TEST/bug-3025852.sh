#! /usr/bin/env bash
bug=3025852
if [[ $1 == "--hwut-info" ]]; then
    echo "attardi: $bug 0.49.2 Instatiation of inheritable-only-modes"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i simple.qx -o Simple --comment-mode-patterns --debug-exception

echo "Search for THE_INHERITABLE_ONLY_MODE_XYZ_4711 ___________________________"
echo " (No output is good output. '*' indicates that it appears in comment)"
grep THE_INHERITABLE_ONLY_MODE_XYZ_4711 Simple Simple.cpp

echo
echo "Compilation _____________________________________________________________"
echo " (No output is good output)"
g++ -Wall -c Simple.cpp -o Simple.o -I. -I$QUEX_PATH
echo
echo "Result of: > ls Simple.o ________________________________________________"
ls Simple.o
echo
echo "_________________________________________________________________________"

rm Simple*

# cleansening
cd $tmp
