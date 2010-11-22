#! /usr/bin/env bash
bug=3097431
if [[ $1 == "--hwut-info" ]]; then
    echo "yaroslavkrv: $bug 0.54.1 Line-Column numbers"
    exit
fi

tmp=`pwd`
cd $bug/ 
make >& tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
./lexer ./match-1.asm
rm tmp.txt

# cleansening
make clean >& /dev/null
cd $tmp
