#! /usr/bin/env bash
./EXE $1 &> tmp.txt
source $QUEX_PATH/TEST/quex_pathify.sh tmp.txt
