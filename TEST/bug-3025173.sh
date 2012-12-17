#! /usr/bin/env bash
bug=3025173
if [[ $1 == "--hwut-info" ]]; then
    echo "alexeevm: $bug 0.49.2 Custom Token struct for quex"
    exit
fi

tmp=`pwd`
cd $bug/ 

echo "(1) Generate 'OK-Sources' and Compile"
quex -i scan.qx -o br_scan --token-class-file token.h --token-id-prefix BR_TKN_ --foreign-token-id-file gramma.h --token-class blackray::Token --debug-exception >& tmp.txt
# File 'check' will only be there, if the compilation was successful
rm -f check
g++ -Wall br_scan.cpp example.cpp -I$QUEX_PATH -I. -o check >& tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
ls check
rm -f check
rm -f tmp.txt
rm -f br_scan*

echo "(2) Mix member assignments with manually written token class."
quex -i scan-error.qx -o br_scan --token-class-file token.h --token-id-prefix BR_TKN_ --foreign-token-id-file gramma.h --token-class blackray::Token
rm -f br_scan*

echo "(3) Provide a 'token_type' definition together with a manually written class."
quex -i CppDefault.qx scan.qx -o br_scan --token-class-file token.h --token-id-prefix BR_TKN_ --foreign-token-id-file gramma.h --token-class blackray::Token
rm -f br_scan*

echo "(4) Manually written token class without '--token-class' definition"
quex -i scan.qx -o br_scan --token-class-file token.h --token-id-prefix BR_TKN_ --foreign-token-id-file gramma.h  


# cleansening
make clean >& /dev/null
cd $tmp
