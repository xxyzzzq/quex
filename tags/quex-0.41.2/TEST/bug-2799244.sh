#! /usr/bin/env bash
bug=2799244
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug 0.39.5 attempts to call unimplemented token set() function;"
    echo "CHOICES: error, good-1, good-2, test;"
    exit
fi

tmp=`pwd`
cd $bug/ 
if [[ $1 == "test" ]]; then
    echo "(*) 'char' and 'wstring'"
    echo
    quex -i $1.qx -o Simple -b 1
    echo "(*) 'wchar_t' and 'wstring'"
    echo
    quex -i $1.qx -o Simple -b wchar_t
else
    echo "(*) Full Error"
    echo
    quex -i $1.qx -o Simple
    if [[ $1 == "error" ]]; then
        echo "(*) No String Accumulator"
        echo
        quex -i $1.qx -o Simple --nsacc
    else
        echo "(*) perform compilation"
        g++ -I$QUEX_PATH -I. -c *.cpp -Wall
    fi
fi


# cleansening
rm -f Simple* 
cd $tmp
