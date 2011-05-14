#! /usr/bin/env bash
bug=2841726
if [[ $1 == "--hwut-info" ]]; then
    echo "nobody: $bug 0.44.2 Unknown exception on unicode properties"
    exit
fi

cat << EOF
##
## The reported error appears when python is compiled with 'narrow build'.
## This build options disallows the usage of unicode characters > 0xFFFF.
##
## In particular the function 'unichr()' will throw an error. This test
## checks if this function is used in the source code. If this happens,
## please, replace 'unichr(N)' with 'eval("u'\\U%08X'" % N)'.
##
EOF

grep -sHIne '\bunichr\b' `find $QUEX_PATH -name "*.py"`

