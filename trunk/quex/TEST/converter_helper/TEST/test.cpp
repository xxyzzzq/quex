#define QUEX_NAMESPACE_MAIN_OPEN  namespace Tester {
#define QUEX_NAMESPACE_MAIN_CLOSE }

#define ____QUEX_CONVERTER_HELPER(A, B) Testy_from_ ## A ## _to_ ## B
#define __QUEX_CONVERTER_HELPER(A, B)   ____QUEX_CONVERTER_HELPER(A, B)

#define QUEX_TYPE_CHARACTER   uint32_t

#if   defined(TEST_UTF8)
#  include <quex/code_base/converter_helper/utf8>
#  include <quex/code_base/converter_helper/utf8.i>
#  define  CODEC utf8
#elif defined(TEST_UTF16)
#  include <quex/code_base/converter_helper/utf16>
#  include <quex/code_base/converter_helper/utf16.i>
#  define  CODEC utf16
#elif defined(TEST_UTF16)
#elif defined(TEST_UNICODE)
#  include <quex/code_base/converter_helper/unicode>
#  include <quex/code_base/converter_helper/unicode.i>
#  define  CODEC unicode
#elif defined(TEST_CODEC)
#else
#  error "No test codec defined."
#endif

#define CONVERTER(OUTPUT)   Tester::__QUEX_CONVERTER_HELPER(CODEC, OUTPUT)

using namespace std;
#include <iostream>

template <class DrainT> void
check_output(const DrainT* Drain, const DrainT* DrainEnd, const DrainT* ref_iterator)
{
    const DrainT* iterator = Drain;

    if( iterator > DrainEnd ) { cout << "Drain Distorted\n"; return; }

    for(; iterator != DrainEnd; ++iterator) {
        if( *ref_iterator != *iterator ) { 
            cout << "At element " << (size_t)(iterator - Drain) << ": ERROR!\n"; 
            return; 
        }
    }
    cout << "Checked " << (size_t)(iterator - Drain) << " elements: GOOD!\n"; 
}

void 
output_utf8_string(const char*                 TestName, 
                   const QUEX_TYPE_CHARACTER*  source_p,
                   const QUEX_TYPE_CHARACTER*  SourceEnd,
                   size_t                      DrainSize,
                   const uint8_t*              reference)
{
    cout << TestName << "____________________________________________________\n";
    cout << endl;
    cout << "Convert the 'C' way\n";
    {
        uint8_t*         drain    = new uint8_t[DrainSize]; 
        uint8_t*         drain_p  = drain;
        const uint8_t*   DrainEnd = drain + DrainSize;

        CONVERTER(utf8_string)(&source_p, SourceEnd, &drain_p,  DrainEnd);
        check_output(drain, drain_p, reference);
        delete drain;
    }

    cout << "Convert the 'C++' way\n";
    {
        std::basic_string<QUEX_TYPE_CHARACTER>  source;
        std::string                             drain;

        drain = CONVERTER(utf8_string)(source);
        check_output<char>(drain.c_str(), drain.c_str() + drain.length(), (const char*)reference);
    }
    cout << endl;
}

int
main(int argc, char** argv)
{
    {
        QUEX_TYPE_CHARACTER*  source = 0x0;
        output_utf8_string("Empty Source", source, source, 1024, 0x0);
    }
}
