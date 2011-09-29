#! /usr/bin/env bash
bug=3295781
if [[ $1 == "--hwut-info" ]]; then
    echo "remcobloemen1: $bug Duplicate label with Template and Path Compression"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i test.qx -o Simple --template-compression 1 --path-compression --language C > tmp.txt
gcc -I${QUEX_PATH} -c Simple.c -Wall >> tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
rm tmp.txt

# cleansening
rm Simple*
cd $tmp

