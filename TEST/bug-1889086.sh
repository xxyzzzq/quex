#! /usr/bin/env bash
bug=1889086
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug Single state mode causes quex to crash"
    exit
fi

tmp=`pwd`
cd $bug 
pwd
echo "tokens in .qx files _____________________________________"
echo '(1)'
quex -i error-1.qx --engine Simple
echo '(2)'
quex -i error-2.qx --engine Simple
echo '(3)'
quex -i error-3.qx --engine Simple
echo 
echo "tokens on command line __________________________________"
echo '(1)'
quex --token-prefix TKN-
echo '(2)'
quex --token-prefix SMOEREBROED
rm -f Simple  Simple-core-engine.cpp  Simple.cpp  Simple-token_ids
cd $tmp
