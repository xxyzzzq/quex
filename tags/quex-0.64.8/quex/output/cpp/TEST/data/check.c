#include <data/check.h>


int
main(int argc, char** argv)
{
    FILE*                 fh = fopen(DEF_FILE_NAME, "rb");
    size_t                n  = 0;
    QUEX_TYPE_CHARACTER   buffer[65536];
    QUEX_TYPE_ANALYZER    me;
    

    if( fh == NULL ) {
        printf("Could not open file.\n");
        return -1;
    }

    n = fread((void*)buffer, sizeof(QUEX_TYPE_CHARACTER), 65536, fh);

    me.counter._column_number_at_end = 0;
    me.counter._line_number_at_end   = 0;
    DEF_COUNTER_FUNCTION(&me, &buffer[0], &buffer[n]);

    printf("file:     '%s';\n"
           "char_size: %i;\n" 
           "byte_n:    %i;\n", DEF_FILE_NAME, sizeof(QUEX_TYPE_CHARACTER), (int)n);
    printf("column_n:  %i;\n"
           "line_n:    %i;\n", 
           (int)me.counter._column_number_at_end,
           (int)me.counter._line_number_at_end);

    return 0;
}
