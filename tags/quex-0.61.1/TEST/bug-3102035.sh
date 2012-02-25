#! /usr/bin/env bash
bug=3102035
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug 0.55.1 Weird Setup causes Duplicate State Label"
    echo "CHOICES: 1, 2, 3, 4, 5;"
    exit
fi

cat << EOF
## In this test we try to avoid issues with some 'weird' cases that
## produced duplicate state labels. The the compiler warnings such as
## 
##   Case3.c:154: error: duplicate label ‘STATE_39’
##   Case3.c:151: error: previous definition of ‘STATE_39’ was here
##
## would appear. If they do not, then everything is fine.
EOF

tmp=`pwd`
cd $bug/ 
make Case$1 >& tmp.txt

case $1 in 
    4) ./Case4 mini.txt >& tmp.txt;;
    5) ./Case5 mini.txt >& tmp.txt;;
esac

../quex_pathify.sh tmp.txt

# cleansening
make clean >& /dev/null
cd $tmp
