#! /usr/bin/env bash
bug=2896732
if [[ $1 == "--hwut-info" ]]; then
    echo "nazim-can-bedir: $bug 0.46.2 - Memory leak"
    exit
fi
echo "Note: the important phrase is 'no leaks are possible'."
tmp=`pwd`
cd $bug/ 
./compile.sh >& tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
valgrind -v --leak-check=full ./uXa example.txt >& tmp.txt
python ./show.py 
rm tmp.txt

# cleansening
./clean.sh
cd $tmp
