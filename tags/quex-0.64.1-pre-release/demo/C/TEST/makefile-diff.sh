#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "Makefile Differences to C++ Version;"
    echo "CHOICES:  000, 001, 002, 003, 005, 006, 007, 008, 009, 010, 011, 012, 012b;"
    exit
fi
diff --ignore-tab-expansion \
     --ignore-space-change  \
     --ignore-all-space     \
     --ignore-blank-lines   \
     $QUEX_PATH/demo/Cpp/$1/Makefile \
     $QUEX_PATH/demo/C/$1/Makefile | awk '! /[0-9]+[a-z]+[0-9]+/'
     # --ignore-matching-lines=RE
