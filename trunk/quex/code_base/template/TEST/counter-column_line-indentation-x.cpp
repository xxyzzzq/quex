#include <my_tester.h>
#include <iostream>
#include <cstring>

using namespace std;
using namespace quex;


string    total_string;
int       indentation[64];
mini_mode tester_mini_mode;

void
print(CounterWithIndentation& x, const char* TestString)
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
test(const char* TestString, CounterWithIndentation& x)
{
    x.__shift_end_values_to_start_values();
    x.icount((QUEX_CHARACTER_TYPE*)TestString, (QUEX_CHARACTER_TYPE*)TestString + strlen(TestString));
    print(x, TestString);
}

void 
test_NoNewline(const char* TestString, CounterWithIndentation& x)
{
    x.__shift_end_values_to_start_values();
    x.icount_NoNewline((QUEX_CHARACTER_TYPE*)TestString, strlen(TestString));
    print(x, TestString);
}

void 
test_NoNewline_NeverStartOnWhitespace(const char* TestString, CounterWithIndentation& x)
{
    int line_n = 0;
    for(const char* p=TestString; *p ; ++p) if( *p == '\n' ) ++line_n; 

    x.__shift_end_values_to_start_values();
    x.icount_NoNewline_NeverStartOnWhitespace(strlen(TestString));
    print(x, TestString);
}

void 
test_NoNewline_ContainsOnlySpace(const char* TestString, CounterWithIndentation& x)
{
    int line_n = 0;
    for(const char* p=TestString; *p ; ++p) if( *p == '\n' ) ++line_n; 

    x.__shift_end_values_to_start_values();
    x.icount_NoNewline_ContainsOnlySpace(strlen(TestString));
    print(x, TestString);
}

int
main(int  argc, char** argv)
{
    my_tester                y;
    CounterWithIndentation   x(&y);
    y.counter = &x;
    x._line_number_at_end = 1;
        
    if( argc > 1 and string(argv[1]) == "--hwut-info" ) {
        cout << "Count Line and Column: With Indentation II\n";
        return 0;
    }

    // x.__buffer->__the_end = (QUEX_CHARACTER_TYPE*)0xFFFFFFFFL;

    // indentation[i] is going to be filled by: mini_mode::on_indentation(my_tester* x, int Indentation) 
    for(int i=0; i < 64; ++i) indentation[i] = 66;

    test("  [23", x);
    test("\n", x);
    test("\n   [bc", x);
    test_NoNewline_NeverStartOnWhitespace("[23   ", x);
    test("\n   ", x);
    test_NoNewline_ContainsOnlySpace("   ", x);
    test_NoNewline("   [YZ", x);
    test("\n   [BC\n   123", x);
    test("\n   [23\n    ", x);
    test_NoNewline_NeverStartOnWhitespace("[bc", x);
    test("\n123\n    ", x);
    test_NoNewline_NeverStartOnWhitespace("[BC", x);
    test("\n\n\n123    ", x);
    test("[YZ\n\n\n  123   \n", x);
    test_NoNewline_NeverStartOnWhitespace("[234567890", x);

    cout << "\n";
    cout << "Total String:\n";
    cout << "001: [" << indentation[0] << "] ";
    int line_n = 1;
    char tmp[6];
    for(size_t i = 0; i < total_string.length() ; ++i) {
        if( total_string[i] == '\n' ) {
            ++line_n;
            if( indentation[line_n - 1] == 66 ) 
                sprintf(tmp, "%03i: [ ] ", line_n);
            else
                sprintf(tmp, "%03i: [%i] ", line_n, indentation[line_n-1]);
            cout << "\\" << endl << tmp;
        } else if( total_string[i] == ' ' ) {
            cout << ".";
        } else {
            cout << total_string[i];
        }
    }

    cout << endl;
}
