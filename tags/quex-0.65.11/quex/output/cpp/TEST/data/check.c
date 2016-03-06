#include <data/check.h>
#include <string.h>


int
main(int argc, char** argv)
{
    FILE*                 fh = fopen(DEF_FILE_NAME, "rb");
    size_t                n  = 0;
    QUEX_TYPE_LEXATOM   buffer[65536];
    QUEX_TYPE_ANALYZER    me;
    int                   verbose_f = (argc > 1 && strcmp(argv[1], "verbose") == 0);
    

    if( fh == NULL ) {
        printf("Could not open file.\n");
        return -1;
    }

    n = fread((void*)buffer, sizeof(QUEX_TYPE_LEXATOM), 65536, fh);

    if( verbose_f ) {
        printf("file:     '%s';\n"
               "char_size: %i;\n" 
               "byte_n:    %i;\n", DEF_FILE_NAME, sizeof(QUEX_TYPE_LEXATOM), (int)n);
    }

    me.counter._column_number_at_end = 1;
    me.counter._line_number_at_end   = 1;
    DEF_COUNTER_FUNCTION(&me, &buffer[0], &buffer[n]);

    printf("column_n:  %i;\n"
           "line_n:    %i;\n", 
           (int)me.counter._column_number_at_end,
           (int)me.counter._line_number_at_end);

    return 0;
}
