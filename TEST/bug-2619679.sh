#! /usr/bin/env bash
bug=2619679
if [[ $1 == "--hwut-info" ]]; then
    echo "attardi: $bug QUEX_BUFFER_ASSERT_CONTENT_CONSISTENCY redefined"
    exit
fi

tmp=`pwd`
cd $bug/ 
make clean >& /dev/null
make > tmp.txt
../quex_pathify.sh tmp.txt

# cleansening
make clean >& /dev/null
cd $tmp
