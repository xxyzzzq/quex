#! /usr/bin/env bash
bug=2894648
if [[ $1 == "--hwut-info" ]]; then
    echo "nobody: $bug 0.46.2 Backslashed . is unknown to quex"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i tmp.qx -o Simple --comment-state-machine >& tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
python show.py
rm tmp.txt

# cleansening
rm Simple*
cd $tmp
