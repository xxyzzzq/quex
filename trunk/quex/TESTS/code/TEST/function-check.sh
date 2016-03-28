# Find all function definitions 
function_list=$(mktemp)
grep -shoe "^ *def *[a-zA-Z_0-9]*(" /home/fschaef/prj/quex/trunk/quex -r --include "*.py" \
| awk '{ print $2; }' \
| sort -u \
| tr -d "(" > $function_list

function_mentioned=$(mktemp)
grep -sHIne "\b[a-zA-Z_0-9]*(" /home/fschaef/prj/quex/trunk/quex -r --include "*.py" \
| tr -d "(" > $function_mentioned

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
    if [[ "${array:0}" = "U" ]]; then
        grep -shoe ${array:1} $QUEX_PATH -r --include "*.py" \
        | awk '{ print $0 " function defined but not used."; }'
    else
        grep -shoe ${array:1} $QUEX_PATH -r --include "*.py" \
        | awk '{ print $0 " solely locally used function does not begin with '_'"; }'
    fi

done < $issue


