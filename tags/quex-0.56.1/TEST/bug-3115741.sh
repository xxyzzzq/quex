#! /usr/bin/env bash
bug=3115741
if [[ $1 == "--hwut-info" ]]; then
    echo "jmarsik: $bug 0.55.4 move_backward triggers assert"
    echo "CHOICES: general, undo-line-colum-count;"
    exit
fi

if [[ $1 == "general" ]]; then
    choice=example
else
    choice=undo-line-column-count
fi


tmp=`pwd`
cd $bug/ 

make clean >& /dev/null

make QX_FILE=$choice.qx >& tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
rm tmp.txt

./lexer $choice.txt

# cleansening
make clean >& /dev/null
cd $tmp
