#! /usr/bin/env bash
bug=2914877
if [[ $1 == "--hwut-info" ]]; then
    echo "prade2p: $bug 0.47.3 RE Exception on [10000-10FFFF]"
    exit
fi

tmp=`pwd`
cd $bug/ 
echo "file list before:"
ls
quex -i test.qx -o Simple  -b 4 >& tmp.txt
echo
echo "quex: no output is just fine."
cat tmp.txt 
rm tmp.txt
echo
echo "file list after:"
ls

# cleansening
rm Simple*
cd $tmp
