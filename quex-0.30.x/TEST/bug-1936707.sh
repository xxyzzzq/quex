#! /usr/bin/env bash
bug=1936707
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug 0.24.10 --plot flag doesnt seem to work"
    exit
fi

tmp=`pwd`

# (*) Create a screwed-up version of 'dot' the graphviz package.
echo "#! /usr/bin/env bash"                          >  $bug/dot
# NOTE: The 'VIZ' is written weirdly so that quex doesn't find the keyword 'Graphviz'
#       or similar variations.
echo "echo \"I am a screwed-up version of 'dot' (GraphVIZ)\"" >> $bug/dot
chmod u+x $bug/dot

cd $bug/ 
# (1) First, let's try with the 'good' dot program
echo "(1) Run with 'dot' available"
quex -i error.qx -o Simple --plot svg
echo

# (2) Second, Let's screw the PATH variable so that quex finds the screwed 'dot'
#     application in the bug's directory:
echo "(2) Run without 'dot' available"
export PATH=`pwd`:$PATH
quex -i error.qx -o Simple --plot svg
echo

# (3) First, let's try with the 'good' dot program
echo "(3) Run with missing command line argument"
quex -i error.qx -o Simple --plot 
echo

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simplism dot X.svg
cd $tmp
