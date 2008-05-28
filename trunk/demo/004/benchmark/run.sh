stamp=`date +%Yy%mm%dd-%Hh%M`
output="result-$stamp.dat"
cd ..
make clean; make OPTIMIZATION='-O3'
cd benchmark
../lexer-lc many-tiny-tokens.c            > $output
../lexer-lc single-large-token.c         >> $output
../lexer-lc linux-2.6.22.17-kernel-dir.c >> $output

../lexer many-tiny-tokens.c           >> $output
../lexer single-large-token.c         >> $output
../lexer linux-2.6.22.17-kernel-dir.c >> $output

cd ..
make clean; make OPTIMIZATION='-Os'
cd benchmark
../lexer-lc many-tiny-tokens.c           >> $output
../lexer-lc single-large-token.c         >> $output
../lexer-lc linux-2.6.22.17-kernel-dir.c >> $output

../lexer many-tiny-tokens.c           >> $output
../lexer single-large-token.c         >> $output
../lexer linux-2.6.22.17-kernel-dir.c >> $output

