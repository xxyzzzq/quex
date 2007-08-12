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
if [[ $1 == "QuexCore" ]]; then
    makefile_name=Makefile
fi
if [[ $1 == "FlexCore" ]]; then
    makefile_name=Makefile.flex_core
fi
cd $QUEX_PATH/demo/$2
pwd
echo "makefile =" $makefile_name
echo "cleaning ..."
make -f $makefile_name clean >& /dev/null
echo "building ..."
make -f $makefile_name       >& /dev/null
echo "executing ..."
./lexer
echo "cleaning ..."
make -f $makefile_name clean >& /dev/null

