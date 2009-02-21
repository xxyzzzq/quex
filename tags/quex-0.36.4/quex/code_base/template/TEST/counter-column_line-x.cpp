#include <my_tester.h>
#include <cstring>
#include <iostream>
#include <string>

using namespace std;
using namespace quex;

string total_string;

int    indentation[64];


void
print(Counter& x, const char* TestString)
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
test(const char* TestString, Counter& x)
{
    x.__shift_end_values_to_start_values();
    x.count((QUEX_CHARACTER_TYPE*)TestString, (QUEX_CHARACTER_TYPE*)TestString + strlen(TestString));
    print(x, TestString);
}

void 
test_NoNewline(const char* TestString, Counter& x)
{
    x.__shift_end_values_to_start_values();
    x.count_NoNewline(strlen(TestString));
    print(x, TestString);
}

void 
test_FixedNewlineN(const char* TestString, Counter& x)
{
    int line_n = 0;
    for(const char* p=TestString; *p ; ++p) if( *p == '\n' ) ++line_n; 

    x.__shift_end_values_to_start_values();
    x.count_FixNewlineN((QUEX_CHARACTER_TYPE*)TestString, 
                        (QUEX_CHARACTER_TYPE*)TestString + strlen(TestString), line_n);
    print(x, TestString);
}


int
main(int  argc, char** argv)
{
    Counter   x;
        
    if( argc > 1 and strcmp(argv[1], "--hwut-info") == 0 ) {
        cout << "Count Line and Column: Without Indentation Count II\n";
        return 0;
    }

    // x.__buffer->__the_end = (QUEX_CHARACTER_TYPE*)0xFFFFFFFFL;

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
