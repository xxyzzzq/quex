#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/009: Standard Input (stdin/cin);"
    exit
fi
cd $QUEX_PATH/demo/Cpp/009

make stdinlexer >& /dev/null

echo -e "Hello World\nbye\n" | valgrind --leak-check=full ./stdinlexer &>  tmp.txt
echo -e "212 W32orld\nbye\n" | valgrind --leak-check=full ./stdinlexer &>> tmp.txt
python $QUEX_PATH/TEST/show-valgrind.py 

make clean &> /dev/null

