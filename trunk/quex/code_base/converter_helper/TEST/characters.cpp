extern "C" { 
#include <iconv.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
}
#include "common.h"

#define UTF8_STRING_SIZE  6
#define UTF16_STRING_SIZE 6
#define UTF32_STRING_SIZE 6

struct UnicodeTester {
    iconv_t   to_utf8;
    iconv_t   to_utf16;
    size_t    error_n;

    UnicodeTester() {
        to_utf8  = iconv_open("UTF8", "UCS4");  

        if( to_utf8 == (iconv_t)-1 ) { 
            std::printf("Error no conversion handle."); std::exit(0); 
        }

        to_utf16 = iconv_open("UTF-16LE", "UCS4");
        if( to_utf16 == (iconv_t)-1 ) { 
            std::printf("Error no conversion handle."); std::exit(0); 
        }

        error_n = 0;
    }

    bool get_utf8_and_utf16(uint32_t UTF32Source, uint8_t  utf8_source[5], uint16_t utf16_source[2]) 
    {
        size_t    report         = 0;
        uint8_t   utf32_memory[4];
        uint8_t*  utf32_source = utf32_memory;
        
        utf32_memory[3] = UTF32Source & 0xFF;
        utf32_memory[2] = (UTF32Source >> 8) & 0xFF;
        utf32_memory[1] = (UTF32Source >> 16) & 0xFF;
        utf32_memory[0] = (UTF32Source >> 24) & 0xFF;
        {
            size_t    in_bytes_left  = 4;
            size_t    out_bytes_left = UTF8_STRING_SIZE;

            utf32_source = utf32_memory;
            memset((void*)utf8_source, 0x0, sizeof(utf8_source));

            report = iconv(to_utf8, (char**)&utf32_source, &in_bytes_left, (char**)&utf8_source, &out_bytes_left);

            if( report == (size_t)-1 ) { 
                // printf("UTF8 Conversion Error for Unicode 0x%06X.\n", (int)UTF32Source);
                return false;
            }
        }
        {
            size_t    in_bytes_left  = 4;
            size_t    out_bytes_left = UTF16_STRING_SIZE;

            utf32_source = utf32_memory;
            memset((void*)utf16_source, 0x0, sizeof(utf16_source));

            report = iconv(to_utf16, (char**)&utf32_source, &in_bytes_left, (char**)&utf16_source, &out_bytes_left);

            if( report == (size_t)-1 ) { 
                // printf("UTF16 Conversion Error for Unicode 0x%06X.\n", (int)UTF32Source);
                return false;
            }
        }

        return true;
    }

    void test_all()
    {
        uint32_t undone_front = (uint32_t)-1;
        uint32_t undone_back  = 0;

        this->error_n = 0;

        for(uint32_t unicode = 0x00000; unicode <= 0x110000; ++unicode) {
            if( test_this(unicode) == false ) {
                if( undone_front == (uint32_t)-1 ) undone_front = unicode;
                undone_back = unicode;
            } else {
                if( undone_front != (uint32_t)-1 ) {
                    printf("No character in [0x%06X, 0x%06X]\n", (int)undone_front, (int)undone_back);
                    undone_front = (uint32_t)-1;
                }
            }
            if( this->error_n > 1000 ) break;
        }
        if( undone_front != (uint32_t)-1 ) {
            printf("No character in [0x%06X, 0x%06X]\n", (int)undone_front, (int)undone_back);
        }

        printf("Errors = %i\n", (int)(this->error_n));
    }

    void check(const char*     Name, 
               const uint8_t*  utf8_expected,  const uint8_t*  utf8_result,
               const uint16_t* utf16_expected, const uint16_t* utf16_result,
               const uint32_t  utf32_expected, const uint32_t  utf32_result)
    {
        if( utf32_expected != utf32_result ) {
            printf("[0x%06X] %s --> UTF32: expected=%06X; result=%06X;\n", (int)utf32_expected, Name, 
                   (int)utf32_expected, (int)utf32_result);
            ++(this->error_n);
        }
        else if(    utf16_expected[0] != utf16_result[0]
                 || utf16_expected[1] != utf16_result[1] ) {
            printf("[0x%06X] %s --> UTF16: expected=%04X.%04X; result=%04X.%04X;\n", (int)utf32_expected, Name, 
                   (int)utf16_expected[0], (int)utf16_expected[1], 
                   (int)utf16_result[0],   (int)utf16_result[1]);
            ++(this->error_n);
        }
        else if(    utf8_expected[0] != utf8_result[0]
                 || utf8_expected[1] != utf8_result[1] 
                 || utf8_expected[2] != utf8_result[2]
                 || utf8_expected[3] != utf8_result[3] ) {
            printf("[0x%06X] %s --> UTF8: expected=%02X.%02X.%02X.%02X; result=%02X.%02X.%02X.%02X;\n", (int)utf32_expected, Name, 
                   (int)utf8_expected[0], (int)utf8_expected[1], (int)utf8_expected[2], (int)utf8_expected[3], 
                   (int)utf8_result[0],   (int)utf8_result[1],   (int)utf8_expected[2], (int)utf8_expected[3]);
            ++(this->error_n);
        }
    }


    bool test_this(uint32_t UTF32Source)
    {
        /* Convert the characters and print the result on the screen. */
        uint8_t*   utf8_drain        = (uint8_t*)malloc((size_t)UTF8_STRING_SIZE);
        uint16_t*  utf16_drain       = (uint16_t*)malloc((size_t)UTF16_STRING_SIZE);
        uint32_t*  utf32_drain       = (uint32_t*)malloc((size_t)UTF32_STRING_SIZE);
        uint8_t*   utf8_drain_p  = utf8_drain;
        uint16_t*  utf16_drain_p = utf16_drain;
        uint32_t*  utf32_drain_p = utf32_drain;

        uint8_t*   utf8_source  = (uint8_t*)malloc((size_t)UTF8_STRING_SIZE);
        uint16_t*  utf16_source = (uint16_t*)malloc((size_t)UTF16_STRING_SIZE);
        uint32_t*  utf32_source = &UTF32Source;
        uint8_t*   utf8_source_p  = utf8_source;
        uint16_t*  utf16_source_p = utf16_source;
        uint32_t*  utf32_source_p = utf32_source;

        if( get_utf8_and_utf16(UTF32Source, utf8_source, utf16_source) == false ) {
            return false;
        }
        {
            memset((void*)utf8_drain,  0x0, UTF8_STRING_SIZE);
            memset((void*)utf16_drain, 0x0, UTF16_STRING_SIZE);
            memset((void*)utf32_drain, 0x0, UTF32_STRING_SIZE);

            utf8_drain_p  = utf8_drain;
            utf16_drain_p = utf16_drain;
            utf32_drain_p = utf32_drain;

            utf8_source_p  = utf8_source; utf16_source_p = utf16_source; utf32_source_p = utf32_source;
            QUEX_CONVERTER_CHAR(utf8, utf8)((const uint8_t**)&utf8_source_p, (uint8_t**)&utf8_drain_p);
            utf8_source_p  = utf8_source; utf16_source_p = utf16_source; utf32_source_p = utf32_source;
            QUEX_CONVERTER_CHAR(utf8, utf16)((const uint8_t**)&utf8_source_p, (uint16_t**)&utf16_drain_p);
            utf8_source_p  = utf8_source; utf16_source_p = utf16_source; utf32_source_p = utf32_source;
            QUEX_CONVERTER_CHAR(utf8, utf32)((const uint8_t**)&utf8_source_p, (uint32_t**)&utf32_drain_p);

            check("From UTF8 ", 
                  utf8_source,  utf8_drain, 
                  utf16_source, utf16_drain, 
                  UTF32Source,  *utf32_drain);
        }
        {
            memset((void*)utf8_drain,  0x0, UTF8_STRING_SIZE);
            memset((void*)utf16_drain, 0x0, UTF16_STRING_SIZE);
            memset((void*)utf32_drain, 0x0, UTF32_STRING_SIZE);

            utf8_drain_p  = utf8_drain;
            utf16_drain_p = utf16_drain;
            utf32_drain_p = utf32_drain;

            utf8_source_p  = utf8_source; utf16_source_p = utf16_source; utf32_source_p = utf32_source;
            QUEX_CONVERTER_CHAR(utf16, utf8)((const uint16_t**)&utf16_source_p, (uint8_t**)&utf8_drain_p);
            utf8_source_p  = utf8_source; utf16_source_p = utf16_source; utf32_source_p = utf32_source;
            QUEX_CONVERTER_CHAR(utf16, utf16)((const uint16_t**)&utf16_source_p, (uint16_t**)&utf16_drain_p);
            utf8_source_p  = utf8_source; utf16_source_p = utf16_source; utf32_source_p = utf32_source;
            QUEX_CONVERTER_CHAR(utf16, utf32)((const uint16_t**)&utf16_source_p, (uint32_t**)&utf32_drain_p);

            check("From UTF16 ", utf8_source,  utf8_drain, 
                  utf16_source, utf16_drain, UTF32Source, *utf32_drain);
        }
        {
            memset((void*)utf8_drain,  0x0, UTF8_STRING_SIZE);
            memset((void*)utf16_drain, 0x0, UTF16_STRING_SIZE);
            memset((void*)utf32_drain, 0x0, UTF32_STRING_SIZE);

            utf8_drain_p  = utf8_drain;
            utf16_drain_p = utf16_drain;
            utf32_drain_p = utf32_drain;

            utf8_source_p  = utf8_source; utf16_source_p = utf16_source; utf32_source_p = utf32_source;
            QUEX_CONVERTER_CHAR(utf32, utf8)((const uint32_t**)&utf32_source_p, (uint8_t**)&utf8_drain_p);
            utf8_source_p  = utf8_source; utf16_source_p = utf16_source; utf32_source_p = utf32_source;
            QUEX_CONVERTER_CHAR(utf32, utf16)((const uint32_t**)&utf32_source_p, (uint16_t**)&utf16_drain_p);
            utf8_source_p  = utf8_source; utf16_source_p = utf16_source; utf32_source_p = utf32_source;
            QUEX_CONVERTER_CHAR(utf32, utf32)((const uint32_t**)&utf32_source_p, (uint32_t**)&utf32_drain_p);

            check("From UTF32 ", utf8_source,  utf8_drain, 
                  utf16_source, utf16_drain, UTF32Source, *utf32_drain);
        }
        return true;
    }


#if 0
    void print(const uint8_t*  utf8_source,  const uint8_t*  utf8_source_end,
               const uint16_t* utf16_source, const uint16_t* utf16_source_end,
               const uint32_t* utf32_source, const uint32_t* utf32_source_end)
    {
        for(uint8_t* p = utf8_drain; p != utf8_iterator; ++utf8_iterator) 
            printf("0x%02x ", (int)*p);
        printf("; ");

        for(uint16_t* p = utf16_drain; p != utf16_iterator; ++utf16_iterator) 
            printf("0x%04x ", (int)*p);

        printf("; ");
        printf("0x%04x;", (int)*p);
    }
#endif
};

#include<support/C/hwut_unit.h>

int
main(int argc, char** argv)
{
    hwut_info("Test of complete character set on base converters (utf8, utf16, utf32);");

    UnicodeTester   tester;
            
    tester.test_all();
}
