#! /usr/bin/env bash
bug=3513568
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug 0.62.2 Memory Leak when using ICU"
    exit
fi

tmp=`pwd`
cd $bug/ 
make >& tmp.txt
cat tmp.txt | awk '(/[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ ' > tmp.log
rm tmp.txt
../quex_pathify.sh tmp.log

echo "Only output shall be: No memory leaks!"
valgrind ./lexer >& tmp.txt
python ../show-valgrind.py tmp.txt

rm tmp.txt

# cleansening
make clean >& /dev/null
cd $tmp
