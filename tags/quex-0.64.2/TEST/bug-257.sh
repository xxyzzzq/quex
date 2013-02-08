#! /usr/bin/env bash
bug=257
if [[ $1 == "--hwut-info" ]]; then
    echo "enmarabrams: $bug Hang-up on recursive --foreign-token-id-file"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i nonsense.qx --foreign-token-id-file include_me.h 2>&1 -o EasyLexer
ls EasyLexer* | sort
rm EasyLexer*
# cleansening
cd $tmp
