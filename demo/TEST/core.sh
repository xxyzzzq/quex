# Unit test for different demos. This is the core file
# All tests follow this structure.
#
#   $1   type of core engine
#   $2   directory where to find the makefile
#
# See 000.sh, 001.sh, 002,sh for examples of tests based on this.
# 
# (C) 2006 Frank-Rene Schäfer
#
#______________________________________________________________________
cd $QUEX_PATH/demo/$2
pwd
echo "makefile =" Makefile
echo "cleaning ..."
make clean >& /dev/null
echo "building ..."
make       >& /dev/null
echo "executing ..."
./lexer
echo "cleaning ..."
make clean >& /dev/null

