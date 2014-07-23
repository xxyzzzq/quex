#! /usr/bin/env bash
bug=2937342
if [[ $1 == "--hwut-info" ]]; then
    echo "attardi: $bug 0.47.3 Regular expression parsing -- closing bracket."
    echo "CHOICES: 1, 2, 3, 4, 5;"
    exit
fi
tmp=`pwd`
cd $bug/ 
x=$1

cat test-$x.qx; 
quex -i test-$x.qx -o Simple

rm -rf Simple*
cd $tmp
