#! /usr/bin/env bash
bug=3510261
if [[ $1 == "--hwut-info" ]]; then
    echo "dlazesz: $bug 0.61.2 Failed "ydd" (0xFF) and begin of line pattern"
    exit
fi

tmp=`pwd`
cd $bug/ 
make >& tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
rm tmp.txt
./test example.txt

# cleansening
make clean >& /dev/null
cd $tmp
