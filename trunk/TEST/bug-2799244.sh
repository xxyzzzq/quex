#! /usr/bin/env bash
bug=2799244
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug 0.39.5 attempts to call unimplemented token set() function;"
    echo "CHOICES: error, good-1, good-2;"
    echo "HAPPY: :[0-9]+;"
    exit
fi

tmp=`pwd`
cd $bug/ 
echo "(*) Full Error"
echo
quex -i $1.qx -o Simple
if [[ $1 == "error" ]]; then
    echo "(*) No String Accumulator"
    echo
    quex -i $1.qx -o Simple --nsacc --debug-exception
else
    echo "(*) perform compilation"
    if [[ $1 == "good-2" ]]; then 
        echo "# Compilation error on return 'Token' instead 'bool'"
        echo "# is intended and correctly expected behavior."
    fi
    g++ -I$QUEX_PATH -I. -c *.cpp -Wall -Werror >& tmp.txt
    cat tmp.txt
    rm  tmp.txt
fi

# cleansening
rm -f Simple* 
cd $tmp
