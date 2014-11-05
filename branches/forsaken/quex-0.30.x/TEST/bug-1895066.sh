#! /usr/bin/env bash
bug=1895066
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug "
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

echo
echo 'Output from constructed header:_______________________________________'
echo
cat Simple | grep -sHne '\#line'

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simplism
cd $tmp
