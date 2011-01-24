stamp=`date +%Yy%mm%dd-%Hh%M`
if [[ $1 != "HWUT-TEST" ]]; then
    output="result-$stamp.dat"
else
    output="tmp.dat"
    rm -f tmp.dat
    cd ..
    make clean >& /dev/null; 
    make lexer OPTIMIZATION=' ' EXTRA_COMPILER_FLAG='-DQUEX_QUICK_BENCHMARK_VERSION' >& /dev/null
    cd run
    ../lexer-quex linux-2.6.22.17-kernel-dir.c > $output
    make clean >& /dev/null; 
    exit
fi

function test_this {
    ./$1 code/many-tiny-tokens.c           >> $output
    ./$1 code/single-large-token.c         >> $output
    ./$1 code/linux-2.6.22.17-kernel-dir.c >> $output
}

echo "" > $output
cd ..
make clean; make COMPILER_OPT='-O3' >& /dev/null
cd run
test_this lexer-quex-lc 
test_this lexer-quex

cd ..
make clean; make COMPILER_OPT='-Os' >& /dev/null
cd run
test_this lexer-quex-lc 
test_this lexer-quex

