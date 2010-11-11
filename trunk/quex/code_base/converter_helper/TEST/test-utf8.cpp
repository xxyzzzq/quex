#ifndef  TEST_UTF8
#   error "TEST_UTF8 must be defined here."
#endif
#include "common.h"
#include <support/C/hwut_unit.h>
#include <cassert>

void
test_this(const QUEX_TYPE_CHARACTER*   Source,
          const uint8_t*               UTF8_Expected,  const size_t  UTF8_DrainSize,
          const uint16_t*              UTF16_Expected, const size_t  UTF16_DrainSize,
          const uint32_t*              UTF32_Expected, const size_t  UTF32_DrainSize)
{
    const QUEX_TYPE_CHARACTER*  source_end = Source;
    for(; *source_end; ++source_end);

    test<uint8_t>("To UTF8", Source, source_end, 
                  UTF8_DrainSize,  UTF8_Expected,
                  CONVERTER(utf8), CONVERTER(utf8)); 
    test<uint16_t>("To UTF16", Source, source_end, 
                   UTF16_DrainSize, UTF16_Expected,
                   CONVERTER(utf16), CONVERTER(utf16)); 
    test<uint32_t>("To UTF32", Source, source_end, 
                   UTF32_DrainSize, UTF32_Expected,
                   CONVERTER(utf32), CONVERTER(utf32)); 
}

int
main(int argc, char** argv)
{
    hwut_info("UTF8 to utf8 and wchar_t.;\n"
              "CHOICES: Normal, Source_Empty, Source_TestFile, Drain_ToSmall;\n"); // Source_Incomplete

    assert( sizeof(QUEX_TYPE_CHARACTER) == 1 );
    
    hwut_if_choice("Normal") {
        QUEX_TYPE_CHARACTER  source[]         = { 0xe4, 0x9c, 0x91 /* Unicode 0x4711 */, 0x0 }; 
        uint8_t              utf8_expected[]  = { 0xe4, 0x9c, 0x91 /* Unicode 0x4711 */, 0x0 }; 
        uint16_t             utf16_expected[] = { 0x4711, 0x0 };
        uint32_t             utf32_expected[] = { 0x00004711, 0x0 };

        test_this(source, utf8_expected, 1024, utf16_expected, 1024, utf32_expected, 1024);
    }
#   if 0
    hwut_if_choice("Source_Empty") {
        QUEX_TYPE_CHARACTER  source[]         = { 0x0 }; 
        uint8_t              utf8_expected[]  = { 0x0 }; 
        wchar_t              wchar_expected[] = { 0x0 };

        test_this(argv[1], source, utf8_expected, 1024, wchar_expected, 1024);
    }
    hwut_if_choice("Source_Incomplete") {
        QUEX_TYPE_CHARACTER  source[]         = { 0xe4, 0x9c, /* 0x91 (Unicode 0x4711) */ 0x0, 0x0, 0x0, 0x0 }; 
        uint8_t              utf8_expected[]  = { 0xe1, 0x89, 0x0, };
        wchar_t              wchar_expected[] = { 0x4711, 0x0 };

        test_this(argv[1], source, utf8_expected, 1024, wchar_expected, 1024);
    }
    hwut_if_choice("Drain_ToSmall") {
        QUEX_TYPE_CHARACTER  source[] = { 0xe4, 0x9c, 0x91, /* unicode 0x4711 */ 
                                          0xe0, 0xa0, 0x95, /* unicode 0x0815 */
                                          0x0 }; 
        uint8_t              utf8_expected[]  = { 0xe4, 0x9c, 0x91 /* unicode 0x4711 */, 0x0 };
        wchar_t              wchar_expected[] = { 0x4711, 0x0 };

        test_this(argv[1], source, utf8_expected, 4, wchar_expected, 1);
    }
    hwut_if_choice("Source_TestFile") {
        QUEX_TYPE_CHARACTER  source[65536];
        QUEX_TYPE_CHARACTER* source_end = read_from_file(source, 65536, "example/utf8.txt");
        uint8_t              utf8_expected[65536];
        wchar_t              wchar_expected[65536];

        memcpy(utf8_expected, source, (source_end - source));
        read_from_file(wchar_expected, 65536, "example/ucs4le.txt");

        test_this(argv[1], source, utf8_expected, 65536, wchar_expected, 65536);
    }
#   endif
}

