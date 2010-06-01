#! /usr/bin/env bash
bug=1908092
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug 0.23.5 uses --token-class without --token-class-file"
    exit
fi

tmp=`pwd`
cd $bug/ 
echo "(1) without --token-class-file"
quex -i error.qx -o Simple 

echo "(2) --token-class-file"
quex -i error.qx -o Simple --token-class-file Otto

echo "(3) --token-class-file without argument"
quex -i error.qx -o Simple --token-class-file 


# cleansening
rm -f Simple  Simple.cpp Simple-token_ids Simplism
cd $tmp
