# Unit test for different demos. This is the core file
# All tests follow this structure.
#
#   $1     directory where to find the makefile
#   $2, $3 arguments passed to the makefile
#
# See 000.sh, 001.sh, 002,sh for examples of tests based on this.
# 
# (C) 2006 Frank-Rene Schäfer
#
#______________________________________________________________________
cd $QUEX_PATH/demo/$1 
if [[ $2 == "NDEBUG" ]]; then
    arg1="NDEBUG_F=-DNDEBUG "
else
    arg1="NDEBUG_F=-DQUEX_OPTION_ACTIVATE_ASSERTS "
fi
echo "makefile =" Makefile
echo "cleaning ..."
make clean   >& /dev/null
echo "make $arg1 $3 ##"
make  $arg1 $3 >& /dev/null
echo "executing ..."
./lexer $args_to_lexer
echo "cleaning ..."
make clean   >& /dev/null

