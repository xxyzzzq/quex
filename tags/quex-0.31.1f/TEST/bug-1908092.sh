#! /usr/bin/env bash
bug=1908092
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug 0.23.5 uses --token-class without --token-class-file"
    exit
fi

tmp=`pwd`
cd $bug/ 
echo "(1) --token-class without --token-class-file"
quex -i error.qx -o Simple --token-class Otto

echo "(2) --token-class without --token-class-file"
quex -i error.qx -o Simple --token-class-file Otto

echo "(3a) --token-class-file without argument"
quex -i error.qx -o Simple --token-class-file --token-class

echo "(3b) --token-class-file without argument"
quex -i error.qx -o Simple  --token-class Otto --token-class-file

echo "(4a) --token-class-file without argument"
quex -i error.qx -o Simple --token-class --token-class-file 

echo "(4b) --token-class-file without argument"
quex -i error.qx -o Simple  --token-class-file Otto --token-class

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simplism
cd $tmp
