#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/009: Strings of 'char' and 'wchar_t'"
    echo "CHOICES:  lexer, wlexer;"
    echo "SAME;"
    exit
fi
cd $QUEX_PATH/demo/Cpp/009
make $1 >& /dev/null
echo "Normal FILE input"
./$1 FILE
echo "Normal stringstream input"
./$1 stringstream
make clean >& /dev/null
