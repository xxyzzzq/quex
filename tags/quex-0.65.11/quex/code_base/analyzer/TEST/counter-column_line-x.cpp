#include <my_tester.h>
#include <cstring>
#include <iostream>
#include <string>

using namespace std;
using namespace quex;

string total_string;

int    indentation[64];


void
print(QUEX_NAME(Counter)& x, const char* TestString)
{
    cout << "__________________________" << endl;
    // cout << "  before: " << x.line_number_at_begin()    << ", " << x.column_number_at_begin() << endl;
    cout << "  lexeme: '";
    for(char* p = (char*)TestString; *p ; ++p) 
       if( *p == '\n' ) cout << "\\n";
       else             cout << *p;
    cout << "'" << endl;
    cout << "  after:  " << x._line_number_at_end    << ", " << x._column_number_at_end << endl;

    total_string += TestString;
}

void 
test(const char* TestString, QUEX_NAME(Counter)& x)
{
    __QUEX_IF_COUNT_LINES(x._line_number_at_begin     = x._line_number_at_end);
    __QUEX_IF_COUNT_COLUMNS(x._column_number_at_begin = x._column_number_at_end);
    QUEX_NAME(Counter_count)(&x, (QUEX_TYPE_LEXATOM*)TestString, (QUEX_TYPE_LEXATOM*)TestString + strlen(TestString));
    print(x, TestString);
}

void 
test_NoNewline(const char* TestString, QUEX_NAME(Counter)& x)
    /* The 'no newline count has been depraced since no advantage can be drawn
     * from it. The number of characters can be counted directly as offset. */
{
    __QUEX_IF_COUNT_LINES(x._line_number_at_begin     = x._line_number_at_end);
    __QUEX_IF_COUNT_COLUMNS(x._column_number_at_begin = x._column_number_at_end);
    // Previously:    QUEX_NAME(Counter_count_NoNewline)(&x, strlen(TestString));
    /* Replacement: */QUEX_NAME(Counter_count)(&x, (QUEX_TYPE_LEXATOM*)TestString, 
                                               (QUEX_TYPE_LEXATOM*)TestString + strlen(TestString));
    print(x, TestString);
}

void 
test_FixedNewlineN(const char* TestString, QUEX_NAME(Counter)& x)
{
    int line_n = 0;
    for(const char* p=TestString; *p ; ++p) if( *p == '\n' ) ++line_n; 

    __QUEX_IF_COUNT_LINES(x._line_number_at_begin     = x._line_number_at_end);
    __QUEX_IF_COUNT_COLUMNS(x._column_number_at_begin = x._column_number_at_end);
    QUEX_NAME(Counter_count_FixNewlineN)(&x, (QUEX_TYPE_LEXATOM*)TestString, 
                                         (QUEX_TYPE_LEXATOM*)TestString + strlen(TestString), line_n);
    print(x, TestString);
}


int
main(int  argc, char** argv)
{
    QUEX_NAME(Counter)   x;
    QUEX_NAME(Counter_construct)(&x); 
        
    if( argc > 1 and strcmp(argv[1], "--hwut-info") == 0 ) {
        cout << "Count Line and Column: Without Indentation Count II\n";
        return 0;
    }

    // x.__buffer->__the_end = (QUEX_TYPE_LEXATOM*)0xFFFFFFFFL;

    test_NoNewline("12345", x);
    test("\n", x);
    test_FixedNewlineN("\n12345", x);
    test_FixedNewlineN("12345\n", x);
    test_NoNewline("123", x);
    test("\n12345", x);
    test_FixedNewlineN("\n12345\n12345", x);
    test("\n12345\n", x);
    test("12345\n12345\n", x);
    test("12345\n\n\n12345", x);
    test_FixedNewlineN("12345\n\n\n12345\n", x);
    test_NoNewline("happy end", x);

    cout << "\n";
    cout << "Total String:\n";
    cout << "001: ";
    int line_n = 1;
    char tmp[6];
    for(size_t i = 0; i < total_string.length() ; ++i) {
        if( total_string[i] == '\n' ) {
            ++line_n;
            sprintf(tmp, "%03i: ", line_n);
            cout << endl << tmp;
        } else {
            cout << total_string[i];
        }
    }
    cout << endl;
}
