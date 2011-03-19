cd $QUEX_PATH/TEST
hwut >& $QUEX_PATH/hwut-output-1.txt &

cd $QUEX_PATH/demo/Cpp/TEST
hwut >& $QUEX_PATH/hwut-output-2.txt &

cd $QUEX_PATH/demo/C/TEST
hwut >& $QUEX_PATH/hwut-output-3.txt &

cd $QUEX_PATH/quex
hwut >& $QUEX_PATH/hwut-output-4.txt

