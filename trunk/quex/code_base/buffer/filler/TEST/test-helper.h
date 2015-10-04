#ifndef __QUEX_INCLUDE_GUARD__BUFFER__PLAIN__TEST__TEST_HELPER_H
#define __QUEX_INCLUDE_GUARD__BUFFER__PLAIN__TEST__TEST_HELPER_H
#include <quex/code_base/buffer/filler/BufferFiller_Plain.i>
#include <cstdio>
#include <iostream>

// Fest gemauert in der Erden
#ifndef QUEX_DEFINED_FUNC_cl_has
static int cl_has(int argc, char** argv, const char* What)
{ return argc > 1 && strcmp(argv[1], What) == 0; }
#endif

#include <quex/code_base/single.i>

inline FILE*
prepare_input()
{
    /* NOTE: This function depends on the compiler setting QUEX_TYPE_CHARACTER */
    const char   test_string[] = "Fest gemauert in der Erden";
    const char*  End           = test_string + strlen(test_string);
    FILE*        fh            = tmpfile();
    /**/
    QUEX_TYPE_CHARACTER character       = (QUEX_TYPE_CHARACTER)0;
    uint8_t*            character_begin = 0x0;

    /* Let's cast using 'real' types, thus ensure that byte-allignment
     * in writing and reading is the same. */
    for(char* p = (char*)test_string; p != (char*)End; ++p) {
        /* Copy the letter into the character according to its alignment */
        character       = (QUEX_TYPE_CHARACTER)*p;
        /* Now, write down the bytes of the character in whatever aligment it was. */
        character_begin = (uint8_t*)&character;
        fwrite(character_begin, sizeof(QUEX_TYPE_CHARACTER), 1, fh);
    }
    fseek(fh, 0, SEEK_SET); /* start reading from the beginning */

    return fh;
}

inline FILE*
prepare_input_error()
{
    /* NOTE: This function depends on the compiler setting QUEX_TYPE_CHARACTER */
    const char   test_string[] = "Fest gemauert in der Erden";
    const char*  End           = test_string + strlen(test_string);
    FILE*        fh            = tmpfile();
    /**/
    QUEX_TYPE_CHARACTER character       = (QUEX_TYPE_CHARACTER)0;
    uint8_t*            character_begin = 0x0;

    /* Let's cast using 'real' types, thus ensure that byte-allignment
     * in writing and reading is the same. */
    char* p = (char*)test_string;
    for(; p != (char*)End - 1; ++p) {
        /* Copy the letter into the character according to its alignment */
        character       = (QUEX_TYPE_CHARACTER)*p;
        /* Now, write down the bytes of the character in whatever aligment it was. */
        character_begin = (uint8_t*)&character;
        fwrite(character_begin, sizeof(QUEX_TYPE_CHARACTER), 1, fh);
    }
    ++p;
    character       = (QUEX_TYPE_CHARACTER)*p;
    /* Now, write down the bytes of the character in whatever aligment it was. */
    character_begin = (uint8_t*)&character;
    fwrite(character_begin, sizeof(QUEX_TYPE_CHARACTER) - 1, 1, fh);

    fseek(fh, 0, SEEK_SET); /* start reading from the beginning */

    return fh;
}

#endif /* __QUEX_INCLUDE_GUARD__BUFFER__PLAIN__TEST__TEST_HELPER_H */
