#! /usr/bin/env bash
bug=3109479
if [[ $1 == "--hwut-info" ]]; then
    echo "mabraham: $bug 0.55.2 Error Transition to Forward Init State" 
    echo "CHOICES: 1, 2, 3, 4;"
    exit
fi

tmp=`pwd`
cd $bug/ 
make clean; make N=$1 >& tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
rm tmp.txt

if [[ $1 == 3 || $1 == 4 ]]; then
    ./lexer example$1.txt
fi

# cleansening
make clean >& /dev/null
cd $tmp
