#! /usr/bin/env bash
bug=3357694
if [[ $1 == "--hwut-info" ]]; then
    echo "denkfix: $bug Matches too long when using certain post condition;"
    echo "CHOICES: Normal, TemplateCompression, PathCompression;"
    echo "SAME;"
    exit
fi

tmp=`pwd`
cd $bug/ 

case $1 in 
    Normal)              make test                                   >& tmp.txt;;
    TemplateCompression) make test ADD_OPTION=--template-compression >& tmp.txt;;
    PathCompression)     make test ADD_OPTION=--path-compression     >& tmp.txt;;
esac

cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
rm tmp.txt
rm -f tmp[01].txt

./test

# cleansening
make clean >& /dev/null
cd $tmp
