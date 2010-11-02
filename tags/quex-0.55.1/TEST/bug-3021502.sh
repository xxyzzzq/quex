#! /usr/bin/env bash
bug=3021502
if [[ $1 == "--hwut-info" ]]; then
    echo "the-user-k: $bug 0.49.2 Buffer-size gets ignored"
    exit
fi

tmp=`pwd`
cd $bug/ 
make  >& tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
./a.out
rm -f tmp.txt

# cleansening
make clean >& /dev/null

cd $tmp
