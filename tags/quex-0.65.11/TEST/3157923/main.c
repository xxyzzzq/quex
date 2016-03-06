#include "Simple.h"
#include "string.h"

int
main(int argc, char** argv)
{
    quex_Simple          qlex;
    FILE*                dummy_fh = fopen("main.c", "rb");
    QUEX_TYPE_LEXATOM* dummy_str = (QUEX_TYPE_LEXATOM*)"Otto";
    QUEX_TYPE_LEXATOM* dummy_str_end = dummy_str + strlen((const char*)dummy_str);

    /* Run this program with valgrind to see whether memory leak occurs. */
    QUEX_NAME(from_memory)(&qlex, 0x0, 0, 0x0);

    QUEX_NAME(Accumulator_add)(&qlex.accumulator, dummy_str, dummy_str_end);

    QUEX_NAME(PostCategorizer_enter)(&qlex.post_categorizer, (QUEX_TYPE_LEXATOM*)"Otto", 12); 

    QUEX_NAME(include_push_FILE)(&qlex, "IncludeName", dummy_fh, 0x0, true);

    QUEX_NAME(destruct)(&qlex);

    QUEX_NAME(from_memory)(&qlex, 0x0, 0, 0x0);
    QUEX_NAME(include_push_FILE)(&qlex, "IncludeName", dummy_fh, 0x0, true);
    QUEX_NAME(reset_FILE)(&qlex, dummy_fh, 0x0, true);
    QUEX_NAME(destruct)(&qlex);
    fclose(dummy_fh);

    return 0;
}
