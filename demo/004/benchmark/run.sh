stamp=`date +%Yy%mm%dd-%Hh%M`
output="result-$stamp.dat"
cd ..
make clean; make
cd benchmark
# blind run, load application, etc. into memory
../lexer many-tiny-tokens.c
# real
../lexer many-tiny-tokens.c           >  $output
../lexer single-large-token.c         >> $output
../lexer linux-2.6.22.17-kernel-dir.c >> $output

# blind run, load application, etc. into memory
../lexer-lc many-tiny-tokens.c
# real
../lexer-lc many-tiny-tokens.c           >> $output
../lexer-lc single-large-token.c         >> $output
../lexer-lc linux-2.6.22.17-kernel-dir.c >> $output

