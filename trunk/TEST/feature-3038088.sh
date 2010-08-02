#! /usr/bin/env bash
bug=3038088
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug token_id = numeric value;"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i simple.qx -o Simple --token-id-offset 111
grep QUEX_TKN Simple-token_ids

# cleansening
rm Simple*
cd $tmp
