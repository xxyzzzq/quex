#include "common.h"


template <class DrainT> void
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


void 
test_utf8_string(const char*                 TestName, 
                 const QUEX_TYPE_CHARACTER*  SourceBegin,
                 const QUEX_TYPE_CHARACTER*  SourceEnd,
                 size_t                      DrainSize,
                 const uint8_t*              reference)
{
    cout << TestName << "____________________________________________________\n";
    cout << endl;
    cout << "...to_utf8_string(... pointers ...)\n";
    {
        const QUEX_TYPE_CHARACTER*  source_p = SourceBegin;
        uint8_t*         drain    = new uint8_t[DrainSize]; 
        uint8_t*         drain_p  = drain;
        const uint8_t*   DrainEnd = drain + DrainSize;

        CONVERTER(utf8_string)(&source_p, SourceEnd, &drain_p,  DrainEnd);
        check(drain, drain_p, reference);
        delete drain;
    }

    cout << "...to_utf8_string(string<QUEX_TYPE_CHARACTER>)\n";
    {
        std::basic_string<QUEX_TYPE_CHARACTER>  source(SourceBegin);
        std::string                             drain;

        drain = CONVERTER(utf8_string)(source);
        if( drain.length() > DrainSize ) {
            cout << "    ## Size of drain is allocated dynamically. Possibly, more gets   ##\n";
            cout << "    ## converted, than expected. Then 'something != 0x0' is no error ##\n";
        }
        check((uint8_t*)drain.c_str(), (uint8_t*)(drain.c_str() + drain.length()), 
              (const uint8_t*)reference);
    }
    cout << endl;
}

void 
test_wstring(const char*                 TestName, 
             const QUEX_TYPE_CHARACTER*  SourceBegin,
             const QUEX_TYPE_CHARACTER*  SourceEnd,
             size_t                      DrainSize,
             const wchar_t*              reference)
{
    cout << TestName << "____________________________________________________\n";
    cout << endl;
    cout << "...to_wstring(... pointers ...)\n";
    {
         const QUEX_TYPE_CHARACTER*  source_p = SourceBegin;
         wchar_t*         drain    = new wchar_t[DrainSize]; 
         wchar_t*         drain_p  = drain;
         const wchar_t*   DrainEnd = drain + DrainSize;

         //printf("BEFORE: Source = %08X; SourceEnd = %08X; (Delta %i); Drain = %08X; DrainEnd = %08X\n", (int)source_p, (int)SourceEnd, (int)(SourceEnd - source_p), (int)drain_p, (int)DrainEnd);
         CONVERTER(wstring)(&source_p, SourceEnd, &drain_p,  DrainEnd);
         //printf("AFTER:  Source = %08X; SourceEnd = %08X; (Delta %i); Drain = %08X; DrainEnd = %08X\n", (int)source_p, (int)SourceEnd, (int)(SourceEnd - source_p), (int)drain_p, (int)DrainEnd);
         check(drain, drain_p, reference);
         delete drain;
    }

    cout << "...to_wstring(string<QUEX_TYPE_CHARACTER>)\n";
    {
        std::basic_string<QUEX_TYPE_CHARACTER>  source(SourceBegin);
        std::wstring                            drain;

        drain = CONVERTER(wstring)(source);
        if( drain.length() > DrainSize ) {
            cout << "    ## Size of drain is allocated dynamically. Possibly, more gets   ##\n";
            cout << "    ## converted, than expected. Then 'something != 0x0' is no error ##\n";
        }
        check((wchar_t*)drain.c_str(), (wchar_t*)(drain.c_str() + drain.length()), 
              (const wchar_t*)reference);
    }
    cout << endl;
}

