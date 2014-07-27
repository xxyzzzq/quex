#! /usr/bin/env bash
bug=1889086
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug Single state mode causes quex to crash"
    exit
fi

tmp=`pwd`
cd $bug 
../quex_pathify.sh --string `pwd`
echo "tokens in .qx files _____________________________________"
echo '(1)'
quex -i error-1.qx -o Simple
echo '(2)'
quex -i error-2.qx -o Simple
echo '(3)'
quex -i error-3.qx -o Simple
echo 
echo "tokens on command line __________________________________"
echo '(1)'
quex --token-id-prefix TKN-
echo '(2)'
quex --token-id-prefix SMOEREBROED
rm -f Simple  Simple.cpp  Simple-token_ids
cd $tmp
