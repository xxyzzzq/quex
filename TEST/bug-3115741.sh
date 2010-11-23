#! /usr/bin/env bash
bug=3115741
if [[ $1 == "--hwut-info" ]]; then
    echo "jmarsik: $bug 0.55.4 move_backward triggers assert"
    exit
fi

tmp=`pwd`
cd $bug/ 
make >& tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
rm tmp.txt

./lexer

# cleansening
make clean >& /dev/null
cd $tmp
