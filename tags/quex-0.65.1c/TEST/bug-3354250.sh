#! /usr/bin/env bash
bug=3354250
if [[ $1 == "--hwut-info" ]]; then
    echo "denkfix: $bug Issue in Hopcroft-Minimization"
    exit
fi

tmp=`pwd`
cd $bug/ 

echo "Stripped Down Scanner:"
echo "(No output is good output)"
quex -i scanner1.qx --icu -b 2 -o Simple >& Simple.txt
cat Simple.txt
echo
echo "Not-So-Stripped Down Scanner:"
echo "(No output is good output)"
quex -i scanner1.qx --icu -b 2 -o Simple >& Simple.txt

rm -f Simple*

cd $tmp
