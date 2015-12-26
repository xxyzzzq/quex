#! /usr/bin/env bash
bug=3538026
if [[ $1 == "--hwut-info" ]]; then
    echo "sbellon: $bug Handling of spurious transition in PathWalkerState"
    exit
fi

# The input files below caused an assertion. It is enough to 
# show that the C files are propperly generated.
tmp=`pwd`
cd $bug/ 

echo "(1) Call Quex: 'No output is good output'"
quex -i token_ids.qx cplusplus.qx --iconv -b 4 --path-compression --template-compression --token-id-prefix Sym_ --debug-exception --language C 2>&1

echo "(2) Check wether generated files are present"
ls Lexer* | sort

rm -f Lexer*

# cleansening
cd $tmp
