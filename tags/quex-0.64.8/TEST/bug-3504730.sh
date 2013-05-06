#! /usr/bin/env bash
bug=3504730
if [[ $1 == "--hwut-info" ]]; then
    echo "clemwang: $bug 0.61.2 Post condition with OR causes crash"
    echo "CHOICES: simple, more;"
    exit
fi

tmp=`pwd`
cd $bug/ 
make $1 >& tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
./$1 $1.txt
rm tmp.txt

# cleansening
make clean >& /dev/null
cd $tmp
