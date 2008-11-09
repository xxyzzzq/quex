#! /usr/bin/env bash
bug=2001787
if [[ $1 == "--hwut-info" ]]; then
    echo "attardi: $bug RE Problem with inverted whitespace"
    exit
fi

echo "** Please note, that '.' in an RE stands for 'anything but newline'   **"
echo "** Thus, it does not match newline, and the lexer triggers on newline **"
echo "** to the default terminal.                                           **"
tmp=`pwd`
cd $bug/ 
make 
./a.out example.txt

# cleansening
make clean
cd $tmp
