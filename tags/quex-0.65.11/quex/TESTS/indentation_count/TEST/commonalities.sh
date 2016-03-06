#! /usr/bin/env bash
if [[ "$1" == "--hwut-info" ]]; then
    echo "Commonalities of Indentation Counter vs. Patterns"
    echo "CHOICES: 1, 2, 3, 4, 5, 5b, 6;"
    exit
fi
echo "## commonalities of the suppressor are no longer forbidden."
quex -i src/error-$1.qx -o Simple   # --debug-exception
rm -f Simple*
