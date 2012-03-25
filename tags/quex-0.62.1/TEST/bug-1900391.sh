#! /usr/bin/env bash
bug=1900391
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug malformed --set-by-expression can crash 0.21.8"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex --set-by-expression 'intersection(\P{ID_Start}, [\x00-\x7f)'

# cleansening
cd $tmp
