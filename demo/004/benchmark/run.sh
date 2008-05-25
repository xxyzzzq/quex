cd ..
make clean; make
cd benchmark
../lexer many-tiny-tokens.c           >> result.db
../lexer single-large-token.c        >> result.db
../lexer linux-2.6.22.17-kernel-dir.c >> result.db

../lexer-l many-tiny-tokens.c           >> result.db
../lexer-l single-large-token.c        >> result.db
../lexer-l linux-2.6.22.17-kernel-dir.c >> result.db

../lexer-lc many-tiny-tokens.c           >> result.db
../lexer-lc single-large-token.c        >> result.db
../lexer-lc linux-2.6.22.17-kernel-dir.c >> result.db

