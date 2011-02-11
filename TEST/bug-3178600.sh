#! /usr/bin/env bash
bug=3178600
if [[ $1 == "--hwut-info" ]]; then
    echo "petulda: $bug 0.58.1 Last appeared char not stored when switching modes"
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
