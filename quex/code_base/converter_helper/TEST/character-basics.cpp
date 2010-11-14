#ifndef  TEST_UTF8
#   error "TEST_UTF8 must be defined here."
#endif
#include "common.h"
#include <support/C/hwut_unit.h>
#include <cassert>



struct Tester {
    iconv_t   to_utf8;
    iconv_t   to_utf16;
    size_t    error_n;

    Tester() {
        to_utf8  = iconv_open("UTF8", "UCS4");  

        if( to_utf8 == (iconv_t)-1 ) { 
            std::printf("Error no conversion handle."); std::exit(); 
        }

        to_utf16 = iconv_open("UTF16", "UCS4") 
        if( to_utf16 == (iconv_t)-1 ) { 
            std::printf("Error no conversion handle."); std::exit(); 
        }

        error_n = 0;
    }

    void get_utf8_and_utf16(uint32_t UTF32Source, uint8_t  utf8_source[5], uint16_t utf16_source[2]) 
    {
        size_t in_bytes_left  = sizeof(uint32_t);
        size_t out_bytes_left = 5;
        size_t report         = 0;
        
        memset((void*)utf8_source, 0x0, sizeof(utf8_source));
        report = iconv(to_utf8, &UTF32Source, &in_bytes_left, utf8_source, &out_bytes_left);

        if( report == (size_t)-1 ) { 
            printf("UTF8 Conversion Error for Unicode 0x%06X.\n", (int)UTF32Source);
        }

        in_bytes_left  = sizeof(uint32_t);
        out_bytes_left = 5;
        report         = 0;
        
        memset((void*)utf16_source, 0x0, sizeof(utf16_source));
        report = iconv(to_utf16, &UTF32Source, &in_bytes_left, utf16_source, &out_bytes_left);

        if( report == (size_t)-1 ) { 
            printf("UTF16 Conversion Error for Unicode 0x%06X.\n", (int)UTF32Source);
        }

    }

    void test_all()
    {
        bool undone_front = (uint32_t)-1;
        bool undone_back  = 0;

        this->error_n = 0;

        for(uint32_t unicode = 0x00000; unicode <= 0x110000; ++unicode) {

            if( test_this(unicode) ) {
                if( undone_front == (uint32_t)-1 ) undone_front = unicode;
                undone_back = unicode;
            } else {
                if( undone_front != (uint32_t)-1 ) {
                    printf("No character in [0x%06X, 0x%06X]\n", (int)undone_front, (int)undone_back);
                    undone_front = (uint32_t)-1;
                }
            }
        }
        if( undone_front != (uint32_t)-1 ) {
            printf("No character in [0x%06X, 0x%06X]\n", (int)undone_front, (int)undone_back);
            undone_front = (uint32_t)-1;
        }

        printf("Errors = %i\n", (int)(this->error_n));
    }

    bool test_this(uint32_t UTF32Source)
    {
        /* Convert the characters and print the result on the screen. */
        uint8_t    utf8_drain[5];
        uint8_t*   utf8_iterator = utf8_drain;
        uint16_t   utf16_drain[2];
        uint16_t*  utf16_iterator = utf16_drain;
        uint32_t   utf32_drain;

        uint8_t    utf8_source[5];
        uint16_t   utf16_source[2];

        if( get_utf8_and_utf16(UTF32Source, utf8_source, utf16_source) == False ) {
            return false;
        }
        {
            memset((void*)utf8_source, 0x0, sizeof(utf8_drain));
            memset((void*)utf16_drain, 0x0, sizeof(utf16_drain));
            utf32_drain = (uint32_t)0;
            __quex_converter_char(utf8, utf8)(&utf8_source, &utf8_drain);
            __quex_converter_char(utf8, utf16)(&utf8_source, &utf16_drain);
            __quex_converter_char(utf8, utf32)(&utf8_source, &utf32_drain);

            check("From UTF8 --> ", utf8_source,  utf8_drain, 
                  utf16_source, utf16_drain, UTF32_source, utf32_drain);
        }
        {
            memset((void*)utf8_source, 0x0, sizeof(utf8_drain));
            memset((void*)utf16_drain, 0x0, sizeof(utf16_drain));
            utf32_drain = (uint32_t)0;
            __quex_converter_char(utf16, utf8)(&utf16_source, &utf8_drain);
            __quex_converter_char(utf16, utf16)(&utf16_source, &utf16_drain);
            __quex_converter_char(utf16, utf32)(&utf16_source, &utf32_drain);

            check("From UTF16 --> ", utf8_source,  utf8_drain, 
                  utf16_source, utf16_drain, UTF32_source, utf32_drain);
        }
        {
            memset((void*)utf8_source, 0x0, sizeof(utf8_drain));
            memset((void*)utf16_drain, 0x0, sizeof(utf16_drain));
            utf32_drain = (uint32_t)0;
            __quex_converter_char(utf32, utf8)(&UTF32Source, &utf8_drain);
            __quex_converter_char(utf32, utf16)(&UTF32Source, &utf16_drain);
            __quex_converter_char(utf32, utf32)(&UTF32Source, &utf32_drain);

            check("From UTF32 --> ", utf8_source,  utf8_drain, 
                  utf16_source, utf16_drain, UTF32_source, utf32_drain);
        }
        return true;
    }

    void check(const uint8_t  utf8_expected[5],  const uint8_t  utf8_result[5],
               const uint16_t utf16_expected[2], const uint16_t utf16_result[2],
               const uint32_t utf32_expected,    const uint32_t utf32_result)
    {
        if( utf32_expected != utf32_result ) {
            printf("%s --> UTF32: expected=%06X; resul=%06X;\n", Name, 
                   (int)utf32_expected, (int)utf32_result);
            ++(this->error_n);
        }
        else if(    utf16_expected[0] != utf16_result[0]
                 || utf16_expected[1] != utf16_result[1] ) {
            printf("%s --> UTF16: expected=%04X.%04X; resul=%04X.%04X;\n", Name, 
                   (int)utf16_expected[0] (int)utf16_expected[1], 
                   (int)utf16_result[0],  (int)utf16_result[1]);
            ++(this->error_n);
        }
        else if(    utf8_expected[0] != utf8_result[0]
                 || utf8_expected[1] != utf8_result[1] 
                 || utf8_expected[2] != utf8_result[2]
                 || utf8_expected[3] != utf8_result[3] ) {
            printf("%s --> UTF8: expected=%02X.%02X.%02X.%02X; resul=%02X.%02X.%02X.%02X;\n", Name, 
                   (int)utf8_expected[0] (int)utf8_expected[1], (int)utf8_expected[2] (int)utf8_expected[3], 
                   (int)utf8_result[0],  (int)utf8_result[1],   (int)utf8_expected[2] (int)utf8_expected[3]);
            ++(this->error_n);
        }
    }

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
};

int
main(int argc, char** argv)
{
    if( argc < 2 ) return 0;

    Tester   tester();
            
    tester.test_all();
}
