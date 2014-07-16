#! /usr/bin/env bash
# PURPOSE: 
# 
# There appeared an issue with respect to CR/LF when files where written and
# saved in DOS format. Normally, quex deals with single LF as line separators.
#
# This test checks whether occurrences of CR/LF (0x0d, 0x0a) as line separator
# causes confusion or difference in the output. For that two input files are
# taken which contain the same information. However, one file 'dos.qx' contains
# CR/LF as line delimiters and the other 'unix.qx' does not.
#
# Both files are input to quex and their output is compared. If it is not 
# equal an error is reported. 
#
# Frank-Rene Schaefer
#------------------------------------------------------------------------------
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: 1885304 Problems with files with DOS CR/LF line endings"
    exit
fi

tmp=`pwd`
pushd 1885304/ 

rm -f Dos* Unix* tmp*.txt

# Generate code from a dos formatted file
echo "Confirm, that 'dos.qx' contains 0x0A 0x0D as newline characters"
cat dos.qx | awk 'BEGIN { RS="--never--" } /\x0d\x0a/ { print; }' | wc
quex -i dos.qx  --engine Xanther
for file in $(ls Xanther*); do cp $file $(echo $file | sed -e 's/Xanther/Dos/g'); done
rm Xanther*

# Generate code from a unix formatted file
echo "Confirm, that 'unix' contains NO 0x0A 0x0D as newline characters"
cat unix.qx | awk 'BEGIN { RS="--never--" } /\x0d\x0a/ { print; }' | wc
quex -i unix.qx --engine Xanther
for file in $(ls Xanther*); do cp $file $(echo $file | sed -e 's/Xanther/Unix/g'); done
rm Xanther*

echo "Watch out, that output from unix file format is the same as from dos format."
echo "DATE stamps are ignored"
echo
ls Dos*
ls Unix*
echo
echo "(*) Dos vs Unix (no output is good output)"
cat Dos  | awk '! /DATE/' > tmp0.txt
cat Unix | awk '! /DATE/' > tmp1.txt
diff tmp0.txt tmp1.txt
echo
for ext in $(echo "-configuration  .cpp  -token -token_ids"); do
    echo "(*) Dos$ext vs Unix$ext (no output is good output)"
    cat Dos$ext  | awk '! /DATE/' > tmp0.txt
    cat Unix$ext | awk '! /DATE/' > tmp1.txt
    diff tmp0.txt tmp1.txt
    echo
done
echo
echo "DONE"

rm -f Dos* Unix* tmp*.txt
popd
