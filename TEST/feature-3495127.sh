#! /usr/bin/env bash
bug=3495127
if [[ $1 == "--hwut-info" ]]; then
    echo "clemwang: $bug Event Handler on_after_match"
    exit
fi

tmp=`pwd`
cd $bug/ 
make >& tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
./a.out example.dat 

# cleansening
rm tmp.txt
make clean >& /dev/null
cd $tmp
