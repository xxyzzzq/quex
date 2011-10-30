#! /usr/bin/env bash
bug=2819045
if [[ $1 == "--hwut-info" ]]; then
    echo "wryun: $bug 0.41.2 Some internal assertion fails on..."
    echo "CHOICES: 0, 1, 2, 3;"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error-$1.qx -o Simple # --debug-exception

# cleansening
rm -f Simple*
cd $tmp
