#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/004: Benchmarking a C-Lexical Analyser"
    exit
fi
cd ../004/benchmark
./run.sh HWUT-TEST
cat tmp.dat | awk '/TokenN/  {print;} /file_name/ {print;}'

