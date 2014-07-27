#! /usr/bin/env bash
bug=2796383
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug 0.39.3 does not handle token_type without distinct section;"
    echo "CHOICES: case-1, case-2, case-3, case-4, case-5;"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i $1.qx -o Simple --suppress 15 --no-string-accumulator
cat Simple-token | awk '/set\_/ { print; } /get\_/ { print; } /union/ { print; } /content/ { print; }'

# cleansening
rm -f Simple*
cd $tmp
