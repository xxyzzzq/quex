#! /usr/bin/env bash
bug=3110544
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug 0.55.2 quex output --intervals with [...]"
    exit
fi

echo "--------------------------------------------------------------------"
echo "quex --set-by-expression [^a] --intervals"
echo
quex --set-by-expression [^a] --intervals

echo "--------------------------------------------------------------------"
echo "quex --set-by-expression [^a] --intervals --numeric"
echo
quex --set-by-expression [^a] --intervals --numeric

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
