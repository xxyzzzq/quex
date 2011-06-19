#! /usr/bin/env bash
bug=2619679
if [[ $1 == "--hwut-info" ]]; then
    echo "attardi: $bug QUEX_BUFFER_ASSERT_CONTENT_CONSISTENCY redefined"
    exit
fi

tmp=`pwd`
cd $bug/ 
make clean >& /dev/null
make

# cleansening
make clean >& /dev/null
cd $tmp
