#! /usr/bin/env bash
bug=3512806
if [[ $1 == "--hwut-info" ]]; then
    echo "ollydbg: $bug 0.62.2 build error"
    echo "CHOICES: C, Cpp;"
    echo "SAME;"
    exit
fi

tmp=`pwd`
echo "## Generation Code for '$1'"                                                                
cd $bug/ 
make $1 >& tmp.txt
echo "No output is good output."
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/ || /Done/) && ! /ASSERTS/ '
rm tmp.txt

# cleansening
make clean >& /dev/null
cd $tmp
