test_dir=../$1
first_f=$2
last_f=$3

if [[ $2 != "FIRST" && $2 != "NOT-FIRST" ]]; then
    echo "Warning: \$2 is not FIRST or NOT-FIRST as HWUT would ask"
fi
if [[ $3 != "LAST" && $3 != "NOT-LAST" ]]; then
    echo "Warning: \$3 is not FIRST or NOT-FIRST as HWUT would ask"
fi

echo $1 $2 $3 >> tmp.txt

current_dir=`pwd`

cd $test_dir

if [[ $first_f == "FIRST" ]]; then
    make clean >& /dev/null
fi
# In any case delete existing object files, and executables
rm -f *.o *.exe

# Make the test program _______________________________________________________
echo "## make lexer $4 $5 $6 $7"
if [[ $args_to_make != "" ]]; then
    make $args_to_make >& tmp-make0.txt
else
    make lexer $4 $5 $6 $7 >& tmp-make0.txt
fi

# Run the test ________________________________________________________________
# (including the check for memory leaks)
if [[ $lexer_name == "" ]]; then
    lexer_name="./lexer"
fi
valgrind $lexer_name $args_to_lexer > tmp-stdout0.txt 2> tmp-stderr0.txt


# Filter important lines ______________________________________________________
# -- filter make results
cat tmp-make0.txt | awk '(  /[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ \
                          || /[Ee][Rr][Rr][Oo][Rr]/)        \
                          && ! /ASSERTS/                    \
                          && ! /deprecated since quex/      \
                          && ! /QUEX_ERROR_EXIT/            \
                          && ! /QUEX_ERROR_DEPRECATED/' > tmp-make.txt

# -- filter experiment results
python $QUEX_PATH/TEST/show-valgrind.py tmp-stdout0.txt > tmp-stdout.txt
python $QUEX_PATH/TEST/show-valgrind.py tmp-stderr0.txt > tmp-stderr.txt

# -- use a 'side-kick' to filter additional lines
#    (caller may copy his side-kick over this one, but
#     note: this file deletes the side-kick.sh!)
if [[ -f $current_dir/side-kick.sh ]]; then
    source $current_dir/side-kick.sh tmp-make.txt  
    source $current_dir/side-kick.sh tmp-stdout.txt 
    source $current_dir/side-kick.sh tmp-stderr.txt 
    # No side-kick.sh of another application shall interfer
    rm -f  $current_dir/side-kick.sh
else
    cat tmp-make.txt  
    cat tmp-stdout.txt 
    cat tmp-stderr.txt 
fi

rm -f tmp-stdout.txt tmp-stdout0.txt
rm -f tmp-stderr.txt tmp-stderr0.txt
rm -f tmp-make.txt   tmp-make0.txt

# Clean up ____________________________________________________________________
if [[ $last_f == "LAST" ]]; then
    make clean >& /dev/null
fi

cd $current_dir
