#! /usr/bin/env bash
bug=3486388
if [[ $1 == "--hwut-info" ]]; then
    echo "clemwang: $bug 0.61.2 Need better errmsg when incorrectly using 2 Lexers at once"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i simple.qx -o Otto  --language C
quex -i simple.qx -o Fritz --language C
gcc  -c lexer.c >& tmp.txt -I$QUEX_PATH
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ ' | head -n 1
rm tmp.txt Fritz* Otto*

# cleansening
make clean >& /dev/null
cd $tmp
