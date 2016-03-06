#! /usr/bin/env bash
bug=3476232
if [[ $1 == "--hwut-info" ]]; then
    echo "rami-al-rafou: $bug 0.62.1 Slow C code generation (unicode)"
    exit
fi

tmp=`pwd`
cd $bug/ 
bash ../test_that_it_does_not_take_too_long.sh simple.qx 20 '--codec utf8' > tmp.txt
../quex_pathify.sh tmp.txt
rm -f Lexer*
cd $tmp
