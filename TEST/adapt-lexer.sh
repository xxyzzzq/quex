cat lexer.cpp | \
awk -v input_file=$1input.txt -v header_file=$1header \
'{ txt = $0; sub("INPUT-FILE", input_file, txt); sub("HEADER", header_file, txt); print txt; }' > $1lexer.cpp

