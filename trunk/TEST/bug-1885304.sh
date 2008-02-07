#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "1885304 by 'sphericalcow': Problems with files with DOS CR/LF line endings"
    exit
fi

tmp=`pwd`
cd 1885304/ 
quex -i dos_lf_2.qx --engine Simple
cat Simple Simple-core-engine.cpp  Simple.cpp  Simple-token_ids | awk ' ! /[dD][aA][tT][eE]/ { print; } ' | awk ' !/AUTO/ { print; }'
rm Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids
cd $tmp
