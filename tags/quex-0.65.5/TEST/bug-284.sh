#! /usr/bin/env bash
bug=284
if [[ $1 == "--hwut-info" ]]; then
    echo "rayhayes: $bug Assert on '--version' (also check for '--help')"
    exit
fi

echo "-----------------------------------------------------------------------"
echo "--version"
echo
quex --version

echo "-----------------------------------------------------------------------"
echo
echo "--help"
echo
quex --help

