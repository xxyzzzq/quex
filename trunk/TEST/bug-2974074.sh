#! /usr/bin/env bash
bug=2974074
if [[ $1 == "--hwut-info" ]]; then
    echo "yoavg: $bug 0.48.1 union modifies its arguments"
    exit
fi

tmp=`pwd`
cd $bug/ 
make >& tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
rm tmp.txt

echo "(*) Test that character sets are not modified."
./the_test example.txt

echo "(*) Test that state machines are not modified."
./the_test example2.txt

# cleansening
make clean >& /dev/null
cd $tmp
