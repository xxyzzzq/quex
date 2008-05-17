#! /usr/bin/env bash
bug=1893849
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug 0.20.5 allows engine names that are not valid identifiers"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Engin-e
rm Engin-e*
cd $tmp
