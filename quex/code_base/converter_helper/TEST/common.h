/* Configure this header by defining one of:
 *
 *    TEST_UTF8, TEST_UTF16, TEST_UNICODE, TEST_CODEC
 *                                                      */
#ifndef __INCLUDE_GUARD__COMMON_H
#define __INCLUDE_GUARD__COMMON_H

#define QUEX_NAMESPACE_MAIN_OPEN  namespace Tester {
#define QUEX_NAMESPACE_MAIN_CLOSE }

#define ____QUEX_CONVERTER_CHAR(FROM, TO)    Tester_ ## FROM ## _to_ ## TO ## _character
#define __QUEX_CONVERTER_CHAR(FROM, TO)      ____QUEX_CONVERTER_CHAR(FROM, TO)
#define ____QUEX_CONVERTER_STRING(FROM, TO)  Tester_ ## FROM ## _to_ ## TO
#define __QUEX_CONVERTER_STRING(FROM, TO)    ____QUEX_CONVERTER_STRING(FROM, TO)

#define QUEX_SETTING_CHAR_CODEC    8
#define QUEX_SETTING_WCHAR_CODEC   32

#if   defined(TEST_UTF8)
#  define  FROM_CODEC           utf8
#  define  QUEX_TYPE_CHARACTER  uint8_t
#  include <quex/code_base/converter_helper/utf8>
#  include <quex/code_base/converter_helper/utf8.i>
#elif defined(TEST_UTF16)
#  define  FROM_CODEC           utf16
#  define  QUEX_TYPE_CHARACTER  uint16_t
#  include <quex/code_base/converter_helper/utf16>
#  include <quex/code_base/converter_helper/utf16.i>
#elif defined(TEST_UTF16)
#elif defined(TEST_UNICODE)
#  define  FROM_CODEC           unicode
#  define  QUEX_TYPE_CHARACTER  uint32_t
#  include <quex/code_base/converter_helper/unicode>
#  include <quex/code_base/converter_helper/unicode.i>
#elif defined(TEST_CODEC)
#else
#  error "No test codec defined."
#endif

#define CONVERTER(OUTPUT)   Tester::__QUEX_CONVERTER_STRING(FROM_CODEC, OUTPUT)

using namespace std;
#include <iostream>
#include <cstdio>
#include <cstdlib>

extern void 
test_utf8_string(const char*         TestName, 
                 const SOURCE_TYPE*  source_p,  const SOURCE_TYPE*  SourceEnd,
                 size_t              DrainSize, const uint8_t*      reference);
extern void 
test_wstring(const char*         TestName, 
             const SOURCE_TYPE*  source_p,  const SOURCE_TYPE*  SourceEnd,
             size_t              DrainSize, const wchar_t*      reference);

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
        for(int i = 0; i < sizeof(ElementT); ++i) {
            int tmp = fgetc(fh);
            if( tmp == EOF ) goto Exit;
            bytes[sizeof(ElementT) - 1 - i] = (uint8_t)tmp;
        }
        ElementT value = 0;
        for(int i = 0; i < sizeof(ElementT); ++i) {
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
        const SOURCE_TYPE*  source_p = SourceBegin;
        DrainT*         drain    = new DrainT[DrainSize]; 
        DrainT*         drain_p  = drain;
        const DrainT*   DrainEnd = drain + DrainSize;

        converter_c_style(&source_p, SourceEnd, &drain_p,  DrainEnd);
        check(drain, drain_p, reference);
        delete drain;
    }

    cout << "with basic_string<" __STRING(SOURCE_TYPE) ">:\n";
    {
        std::basic_string<SOURCE_TYPE>  source(SourceBegin);
        std::basic_string<DrainT>               drain;

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

#endif /* __INCLUDE_GUARD__COMMON_H */
