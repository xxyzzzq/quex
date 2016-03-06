#! /usr/bin/env bash
bug=3030640
if [[ $1 == "--hwut-info" ]]; then
    echo "ymarkovitch: $bug 0.50.1 Adding .hpp extension to generated headers"
    echo "CHOICES: pp, ++, xx, cc, PlainC, PlainCpp, ErrorC, ErrorCpp;"
    exit
fi

tmp=`pwd`
cd $bug/ 

if [[ $1 == "PlainC" ]]; then
    quex -i simple.qx --language C --debug-exception
elif [[ $1 == "ErrorC" ]]; then
    quex -i simple.qx --language C --fes foo # --debug-exception
elif [[ $1 == "PlainCpp" ]]; then
    quex -i simple.qx 
elif [[ $1 == "ErrorCpp" ]]; then
    quex -i simple.qx --fes foo
else
    quex -i simple.qx --fes $1 --debug-exception
fi

# Display the generated files
ls Lexer*

rm Lexer*

cd $tmp
