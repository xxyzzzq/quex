#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/009: Direct Buffer Access (8Bit and WChar Strings)"
    echo "CHOICES:  lexer, wlexer;"
    echo "SAME;"
    exit
fi
cd $QUEX_PATH/demo/009
make $1 >& /dev/null
echo "Normal FILE input"
./$1 FILE
echo "Normal stringstream input"
./$1 stringstream
make clean >& /dev/null
