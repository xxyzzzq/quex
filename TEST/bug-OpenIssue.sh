#! /usr/bin/env bash
bug=OpenIssue
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug 0.55.1 Duplicate State Label"
    echo "CHOICES: 1, 2, 3;"
    exit
fi

# In this test we try to avoid issues with some 'weird' cases that
# produced duplicate state labels. The the compiler warnings such as
# 
#   Case3.c:154: error: duplicate label ‘STATE_39’
#   Case3.c:151: error: previous definition of ‘STATE_39’ was here
#
# would appear. If they do not, then everything is fine.

tmp=`pwd`
cd $bug/ 
make Case$1 >& tmp.txt
echo "No Error, is good output!"

cat tmp.txt
rm tmp.txt

# cleansening
make clean >& /dev/null
cd $tmp
