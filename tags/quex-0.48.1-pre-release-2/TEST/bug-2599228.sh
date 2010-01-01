#! /usr/bin/env bash
bug=2599228
if [[ $1 == "--hwut-info" ]]; then
    echo "attardi: $bug 0.36.1 QUEX_CORE variable not adapted to installed version"
    echo "CHOICES: Developper, Else, FilesExist;"
    exit
fi

echo "The idea behind this test is to see wether the QUEX_CORE variable"
echo "is propperly disabled on systems other then the developper\'s host."
echo "This variable ensures that the unit tests are re-compiled as soon"
echo "as one of the quex headers changes. This is not necessary for"
echo "installed versions of quex."

tmp=`pwd`
cd $bug/ 
export ALWAYS_CORRECT_QUEX_PATH=$QUEX_PATH
if [[ $1 == "Else" ]]; then
    export QUEX_PATH=$1
    make all
elif [[ $1 == "Developper" ]]; then
    make all
else
    echo
    echo This test checks wether all files in QUEX_CORE exist
    echo

    make all > files.txt
    for file in `cat files.txt`; do 
        if ! test -a $file; then
            echo "[FAIL] $file does not exist"
        else
            echo "  [OK] $file exists"
        fi 
    done
    rm -rf files.txt
fi

cd $tmp
