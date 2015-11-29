#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "PRIORITY-MARK or DELETION on not existing pattern.;"
    echo "CHOICES: PRIORITY-good, PRIORITY-fail, DELETION-good, DELETION-fail;"
    exit
fi

quex -i data/$1.qx -o Simple --debug-exception
rm -f Simple*
