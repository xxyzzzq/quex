#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "Makefile Differences;"
    echo "CHOICES:  000, 001, 002, 003, 005;"
    exit
fi
diff --ignore-tab-expansion \
     --ignore-space-change  \
     --ignore-all-space     \
     --ignore-blank-lines   \
     $QUEX_PATH/demo/$1/Makefile \
     $QUEX_PATH/demo/C-beta/$1/Makefile | awk '! /[0-9]+[a-z]+[0-9]+/'
     # --ignore-matching-lines=RE
