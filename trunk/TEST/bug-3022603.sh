#! /usr/bin/env bash
bug=3022603
if [[ $1 == "--hwut-info" ]]; then
    echo "alexeevm: $bug 0.49.2 Using external buffer with Quex lexer"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i simple.qx -o Simple --debug-exception >  tmp.txt 2>  tmp2.txt
g++  point.cpp Simple.cpp -I. -I$QUEX_PATH    >> tmp.txt 2>> tmp2.txt
./a.out                                       >> tmp.txt 2>> tmp2.txt

cat tmp.txt
cat tmp2.txt

rm -f tmp.txt tmp2.txt

# cleansening
rm ./a.out Simple*
cd $tmp
