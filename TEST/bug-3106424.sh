#! /usr/bin/env bash
bug=3106424
if [[ $1 == "--hwut-info" ]]; then
    echo "timdawborn: $bug 0.55.2 --set-by-expression with inverse fails"
    exit
fi

echo "--------------------------------------------------------------------"
echo "quex --set-by-expression [^a] --intervals"
echo
quex --set-by-expression '[^a]' --intervals

echo "--------------------------------------------------------------------"
echo "quex --set-by-expression [^a] --intervals --numeric"
echo
quex --set-by-expression '[^a]' --intervals --numeric

echo "--------------------------------------------------------------------"
echo "quex --set-by-property Script=Greek --intervals"
echo
quex --set-by-property Script=Greek --intervals

echo "--------------------------------------------------------------------"
echo "quex --set-by-property Script=Greek --intervals --numeric"
echo
quex --set-by-property Script=Greek --intervals --numeric

echo "--------------------------------------------------------------------"
echo "quex --set-by-property Script=Greek "
echo
quex --set-by-property Script=Greek 

echo "--------------------------------------------------------------------"
echo quex --set-by-expression '[:inverse([\1-\U10FFFE]):]' --intervals --numeric
echo
quex --set-by-expression '[:inverse([\4-\U10FFFE]):]' --intervals --numeric
