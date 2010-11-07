#ifndef  TEST_UTF8
#   error "TEST_UTF8 must be defined here."
#endif
#include "common.h"
#include <support/C/hwut_unit.h>
#include <cassert>

#define test_this(NAME, SOURCE, REFERENCE, DRAIN_SIZE, W_REFERENCE, W_DRAIN_SIZE) \
        { \
            QUEX_TYPE_CHARACTER Source[] = { SOURCE }; \
            size_t              SourceSize = sizeof(Source) / sizeof(QUEX_TYPE_CHARACTER); \
            { \
                uint8_t  reference[] = { REFERENCE }; \
                test_utf8_string(NAME, Source, Source + SourceSize, DRAIN_SIZE, reference); \
            } \
            { \
                wchar_t  wreference[] = { W_REFERENCE }; \
                test_wstring(NAME, Source, Source + SourceSize, W_DRAIN_SIZE, wreference); \
            } \
        }

int
main(int argc, char** argv)
{
    hwut_info("UTF8 to utf8 and wchar_t.;\n"
              "CHOICES: Normal, Source_Empty, Source_Incomplete, Source_TestFile, Drain_ToSmall;\n");

    assert( sizeof(QUEX_TYPE_CHARACTER) == 1 );
    
#   if 0
    hwut_if_choice("Normal") {
        test_this(/* NAME         */ argv[1],
                  /* SOURCE       */ (0xe4, 0x9c, 0x91 /* Unicode 0x4711 */, 0x0),
                  /* REFERENCE    */ (0xe4, 0x9c, 0x91 /* Unicode 0x4711 */, 0x0),
                  /* DRAIN_SIZE   */ 1024,
                  /* W_REFERENCE  */ (0x4711, 0x0),
                  /* W_DRAIN_SIZE */ 1024);
    }
#   endif
    hwut_if_choice("Normal") {
        QUEX_TYPE_CHARACTER  source[] = { 0xe4, 0x9c, 0x91 /* Unicode 0x4711 */, 0x0 }; 
        {
            uint8_t  reference[] = { 0xe4, 0x9c, 0x91 /* Unicode 0x4711 */, 0x0 }; 
            test_utf8_string(argv[1], source, source + 3, 1024, reference);
        }
        {
            wchar_t  wreference[] = { 0x4711, 0x0 };
            test_wstring(argv[1], source, source + 3, 1024, wreference);
        }
    }
    hwut_if_choice("Source_Empty") {
        QUEX_TYPE_CHARACTER  source = { 0x0 };
        {
            uint8_t  reference = { 0x0 };
            test_utf8_string(argv[1], &source, &source, 1024, &reference);
        }
        {
            wchar_t  wreference = { 0x0 };
            test_wstring(argv[1], &source, &source, 1024, &wreference);
        }
    }
    hwut_if_choice("Source_Incomplete") {
        QUEX_TYPE_CHARACTER  source[] = { 0xe4, 0x9c, /* 0x91 (Unicode 0x4711) */ 0x0 }; 
        {
            uint8_t  reference[] = { 0xe1, 0x89, 0x0 };
            test_utf8_string(argv[1], source, source + 2, 1024, reference);
        }
        {
            wchar_t  wreference[] = { 0x4711, 0x0 };
            test_wstring(argv[1], source, source + 2, 1024, wreference);
        }
    }
    hwut_if_choice("Drain_ToSmall") {
        QUEX_TYPE_CHARACTER  source[] = { 0xe4, 0x9c, 0x91, /* unicode 0x4711 */ 
                                          0xe0, 0xa0, 0x95, /* unicode 0x0815 */
                                          0x0 }; 
        {
            uint8_t  reference[] = { 0xe4, 0x9c, 0x91 /* unicode 0x4711 */, 0x0 }; 
            test_utf8_string(argv[1], source, source + 6, 4, reference);
        }
        {
            wchar_t  wreference[] = { 0x4711, 0x0 };
            test_wstring(argv[1], source, source + 6, 1, wreference);
        }
    }
    hwut_if_choice("Source_TestFile") {
        QUEX_TYPE_CHARACTER  source[65536];
        QUEX_TYPE_CHARACTER* source_end = read_from_file(source, 65536, "example/utf8.txt");
        {
            uint8_t  reference[65536];
            memcpy(reference, source, (source_end - source));
            test_utf8_string(argv[1], source, source_end, 65536, reference);
        }
        {
            wchar_t  wreference[65536];
            read_from_file(wreference, 65536, "example/ucs4le.txt");
            test_wstring(argv[1], source, source_end, 65536, wreference);
        }
    }
}

