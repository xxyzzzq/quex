#! /usr/bin/env bash
bug=2891125
if [[ $1 == "--hwut-info" ]]; then
    echo "nobody: $bug 0.45.1 bug in -- version"
    exit
fi

tmp=`pwd`

cd $QUEX_PATH/quex
echo "## The goal of this test is to find places where quex exits"
echo "## with a 'sys.exit' command. This causes trouble since it"
echo "## may be treated as an exception. No output is good output."
grep -r -E -sHIne "[^a-zA-Z_]exit[ ]*\(" ./ --exclude-dir .svn --exclude-dir TEST --include "*.py" | sed -e 's/:[0-9]\+:/:LineN:/'

cd $tmp
