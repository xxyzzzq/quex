#include "common.h"
#include <support/C/hwut_unit.h>
#include <cassert>

#define CONVERTER(OUTPUT)   __QUEX_CONVERTER_STRING(SOURCE_NAME, OUTPUT)

#include <iostream>
#include <cstdio>
#include <cstdlib>

template <class ElementT> inline ElementT*
read_from_file(ElementT* buffer, size_t Size, const char* FileName)
{
    using namespace std;

    ElementT*   iterator  = buffer;
    ElementT*   BufferEnd = buffer + Size;

    FILE*  fh = fopen(FileName, "rb");
    if( fh == NULL ) {
        printf("File '%s' not found!", FileName);
        exit(-1);
    }

    do {
        uint8_t  bytes[sizeof(ElementT)]; 
        for(size_t i = 0; i < sizeof(ElementT); ++i) {
            int tmp = fgetc(fh);
            if( tmp == EOF ) goto Exit;
            bytes[sizeof(ElementT) - 1 - i] = (uint8_t)tmp;
        }
        ElementT value = 0;
        for(size_t i = 0; i < sizeof(ElementT); ++i) {
            value = (value << 8) | bytes[i];
        }
        *iterator++ = value;
    } while( iterator < BufferEnd - 1 );

Exit:
    *iterator = 0x0; /* Terminating Zero */
    return iterator;
}


template <class SourceT, class DrainT>
struct converter {
    /* This class defines how a function signature of a converter function should look like
     * depending on the DrainT--for both the pointer version and the basic_string<...> version. */
    typedef void                      (*with_pointers_t)(const SourceT**  source_pp, 
                                                         const SourceT*   SourceEnd, 
                                                         DrainT**         drain_pp,  
                                                         const DrainT*    DrainEnd);
    typedef std::basic_string<DrainT> (*with_string_t)(const std::basic_string<SourceT>& Source);

};

template <class DrainT> inline void
check(const DrainT* Drain, const DrainT* DrainEnd, const DrainT* ref_iterator)
{
    const DrainT* iterator = Drain;

    if( iterator > DrainEnd ) { cout << "    ERROR: Drain Distorted\n"; return; }

    for(; iterator != DrainEnd; ++iterator, ++ref_iterator) {
        if( *ref_iterator != *iterator ) { 
            cout << "    ERROR: At element " << (size_t)(iterator - Drain) << ": "; 
            hex(cout);
            cout << " expected: 0x" << (int)*ref_iterator << ", real: 0x" << (int)*iterator << endl; 
            return; 
        }
    }
    dec(cout);
    if( *ref_iterator != (DrainT)0x0 ) {
        cout << "    ERROR: Checked " << (size_t)(iterator - Drain) << " elements: End of reference not reached!\n"; 
    } else {
        cout << "    GOOD: Checked " << (size_t)(iterator - Drain) << " elements.\n"; 
    }
}


template <class SourceT, class DrainT> inline void 
test(const char*     TestName, 
     const SourceT*  SourceBegin, const SourceT*  SourceEnd,
     size_t          DrainSize,   const DrainT*   reference,
     typename converter<SourceT, DrainT>::with_pointers_t   converter_c_style,
     typename converter<SourceT, DrainT>::with_string_t     converter_cpp_style)
{
    cout << TestName << "____________________________________________________\n";
    cout << endl;
    cout << "with pointers:\n";
    {
        const SourceT*  source_p = SourceBegin;
        DrainT*         drain    = new DrainT[DrainSize]; 
        DrainT*         drain_p  = drain;
        const DrainT*   DrainEnd = drain + DrainSize;

        converter_c_style(&source_p, SourceEnd, &drain_p,  DrainEnd);
        check(drain, drain_p, reference);
        delete drain;
    }

    cout << "with basic_string<" __MYSTRING(SOURCE_TYPE) ">:\n";
    {
        std::basic_string<SourceT>  source(SourceBegin);
        std::basic_string<DrainT>   drain;

        drain = converter_cpp_style(source);
        if( drain.length() > DrainSize ) {
            cout << "    ## Size of drain is allocated dynamically. Possibly, more gets   ##\n";
            cout << "    ## converted, than expected. Then 'something != 0x0' is no error ##\n";
        }
        check((DrainT*)drain.c_str(), (DrainT*)(drain.c_str() + drain.length()), 
              (const DrainT*)reference);
    }
    cout << endl;
}

template<class SourceT> void
test_this(const SourceT*     Source,
          const uint8_t*     UTF8_Expected,  const size_t  UTF8_DrainSize,
          const uint16_t*    UTF16_Expected, const size_t  UTF16_DrainSize,
          const uint32_t*    UTF32_Expected, const size_t  UTF32_DrainSize)
{
    using namespace Tester;

    const SourceT*  source_end = Source;
    for(; *source_end; ++source_end) ;

    test<SourceT, uint8_t>("to utf8", Source, source_end, 
                           UTF8_DrainSize,  UTF8_Expected,
                           CONVERTER(utf8), CONVERTER(utf8)); 
    test<SourceT, uint16_t>("to utf16", Source, source_end, 
                            UTF16_DrainSize, UTF16_Expected,
                            CONVERTER(utf16), CONVERTER(utf16)); 
    test<SourceT, uint32_t>("to utf32", Source, source_end, 
                            UTF32_DrainSize, UTF32_Expected,
                            CONVERTER(utf32), CONVERTER(utf32)); 
}

int
main(int argc, char** argv)
{
    hwut_info(__MYSTRING(SOURCE_NAME) " to utf8, utf16, and utf32;\n"
              "CHOICES: Source_Empty, Source_TestFile, Drain_ToSmall;\n"); // Source_Incomplete

    hwut_if_choice("Source_Empty") {
        SOURCE_TYPE  source[]         = { 0x0 }; 
        uint8_t      utf8_expected[]  = { 0x0 }; 
        uint16_t     utf16_expected[] = { 0x0 };
        uint32_t     utf32_expected[] = { 0x0 };

        test_this<SOURCE_TYPE>(source, 
                               utf8_expected,  1024, 
                               utf16_expected, 1024, 
                               utf32_expected, 1024);
    }
#   if 0
    hwut_if_choice("Source_Incomplete") {
        SOURCE_TYPE  source[]         = { 0xe4, 0x9c, /* 0x91 (Unicode 0x4711) */ 0x0, 0x0, 0x0, 0x0 }; 
        uint8_t      utf8_expected[]  = { 0xe1, 0x89, 0x0, };
        uint16_t     utf16_expected[] = { 0x4711, 0x0 };
        uint32_t     utf32_expected[] = { 0x4711, 0x0 };

        test_this<SOURCE_TYPE>(source, 
                               utf8_expected,  1024, 
                               utf16_expected, 1024, 
                               utf32_expected, 1024);
    }
#   endif
    hwut_if_choice("Drain_ToSmall") {
        SOURCE_TYPE  source_utf8[] = { 0xe4, 0x9c, 0x91, /* unicode 0x4711 */ 
                                       0xe0, 0xa0, 0x95, /* unicode 0x0815 */
                                       0x0 }; 
        SOURCE_TYPE  source_utf16_utf32[] = { (SOURCE_TYPE)0x4711, 
                                              (SOURCE_TYPE)0x0815, 
                                              (SOURCE_TYPE)0x0  };
        SOURCE_TYPE* source = 0;

        switch( sizeof(SOURCE_TYPE) ) {
        case 1:  source = source_utf8; break;
        default: source = source_utf16_utf32; break;
        }

        uint8_t   utf8_expected[]  = { 0xe4, 0x9c, 0x91 /* unicode 0x4711 */, 0x0 };
        uint16_t  utf16_expected[] = { 0x4711, 0x0 };
        uint32_t  utf32_expected[] = { 0x4711, 0x0 };

        test_this<SOURCE_TYPE>(source, 
                               utf8_expected,  4, 
                               utf16_expected, 2, 
                               utf32_expected, 1);
    }
    hwut_if_choice("Source_TestFile") {
        SOURCE_TYPE  source[65536];
        uint8_t      utf8_expected[65536];
        uint16_t     utf16_expected[65536];
        uint32_t     utf32_expected[65536];

        read_from_file(utf8_expected,  65536, "example/utf8.txt");
        read_from_file(utf16_expected, 65536, "example/utf16le.txt");
        read_from_file(utf32_expected, 65536, "example/utf32le.txt");

        switch( sizeof(SOURCE_TYPE) ) {
        case 1: memcpy((void*)source, utf8_expected, 65536); break;
        case 2: memcpy((void*)source, utf16_expected, 65536); break;
        case 4: memcpy((void*)source, utf32_expected, 65536); break;
        default: assert(false);
        }

        test_this<SOURCE_TYPE>(source, 
                               utf8_expected,  65536, 
                               utf16_expected, 65536,  /* First word contains 'BOM', so skip that */
                               utf32_expected, 65536);
    }

}

