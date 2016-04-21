# Find all function definitions 
function_list=tmp0.txt # $(mktemp)
function_mentioned=tmp1.txt # $(mktemp)
# | awk '{ print "\"\\b" $2 "\""; }' \

grep -sHoe "^ *def *[a-zA-Z_0-9]*(" $QUEX_PATH -r --include "*.py" \
| awk '{ print $2; }' \
| sort -u \
| tr -d "(" \
> $function_list

wc -w $function_list

grep -she "\\b[a-zA-Z_0-9]*(" $QUEX_PATH -r --include "*.py" \
| grep -ve  "^ *def *" \
| sort -u \
> $function_mentioned
# | tr -d "(" \
# | awk '{ print "^" $0 "\\b"; }' \

wc -w $function_mentioned

function_unused=$(mktemp)
# grep -v -f $function_mentioned $function_list 
# > $function_unused
# | sort -u \
# | awk '{ print "^ *def *" $0 " *("; }' 

wc -w $function_unused
cat $function_unused

echo "Functions defined but never used (no output is good output): {"
grep -sHIne -f $function_unused   
echo "}"

# rm $function_unused
# rm $function_mentioned
# rm $function_list

function unused {
# 1: Print function names which only appear once (in their definition)
#    --> 'U function name'
# 2: Print function names which are only used in the file itself.
#    --> 'N function name'
issues=$(mktemp)
gawk 'BEGIN {                                                         \
          while( getline $function_list ) { db[$0] = ""; }            \
      } {                                                             \
          split($0, fields, ":");                                     \
          file     = fields[0];                                       \
          line     = fields[1];                                       \
          function = fields[2];                                       \
          if( function in db ) {                                      \
              db[function] = db[function] + ":" file;                 \
          }                                                           \
      }                                                               \
      END {                                                           \
          for(function in db) {                                       \
              split(db[function], file_list, ":");                    \
              if( length(file_list) == 0 ) {                          \
                  continue;                                           \
              }                                                       \
              else if( length(file_list) == 1 ) {                     \
                  print "U " function;                                \
              }                                                       \
              else if( function[0] != "_" ) {                         \
                  for( file in file_list ) { count_db[file] += 1; }   \
                  if( length(count_db) == 1 ) {                       \
                      print "N " function;                            \
                  }                                                   \
              }                                                       \
          }                                                           \
      }' > $issues

while read array; do
    if [[ "${array[0]}" = "U" ]]; then
        grep -shoe ${array[1]} $QUEX_PATH -r --include "*.py" \
        | awk '{ print $0 " function defined but not used."; }'
    else
        grep -shoe ${array[1]} $QUEX_PATH -r --include "*.py" \
        | awk '{ print $0 " solely locally used function does not begin with '_'"; }'
    fi

done < $issue
}


