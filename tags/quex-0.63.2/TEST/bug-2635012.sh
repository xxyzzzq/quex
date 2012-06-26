#! /usr/bin/env bash
bug=2635012
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug 0.36.4 Include Stack Disablement"
    exit
fi

tmp=`pwd`
cd $bug/ 
echo "(*) With QUEX_OPTION_INCLUDE_STACK"
make with-include-stack | awk '/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ { print; } /[Ee][Rr][Rr][Oo][Rr]/ { print; }'
echo "(*) With QUEX_OPTION_INCLUDE_STACK_DISABLED"
make without-include-stack | awk '/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ { print; } /[Ee][Rr][Rr][Oo][Rr]/ { print; }'

make clean
cd $tmp
