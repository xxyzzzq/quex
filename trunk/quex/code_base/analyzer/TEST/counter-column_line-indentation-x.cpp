#include <my_tester.h>
#include <iostream>
#include <cstring>

using namespace std;
using namespace quex;


string           total_string;
int              indentation[64];
QUEX_NAME(Mode)  tester_mini_mode;

void
print(QUEX_NAME(CounterLineColumnIndentation)& x, const char* TestString)
{
    cout << "__________________________" << endl;
    // cout << "  before: " << x.line_number_at_begin()    << ", " << x.column_number_at_begin() << endl;
    cout << "  lexeme: '";
    for(char* p = (char*)TestString; *p ; ++p) 
       if( *p == '\n' ) cout << "\\n";
       else             cout << *p;
    cout << "'" << endl;
    cout << "  after:  " << x.base._line_number_at_end    << ", " << x.base._column_number_at_end << endl;

    total_string += TestString;
}

void 
test(const char* TestString, QUEX_NAME(CounterLineColumnIndentation)& x)
{
    QUEX_NAME(CounterBase_shift_end_values_to_start_values)((QUEX_NAME(CounterBase)*)&x);
    QUEX_NAME(CounterLineColumnIndentation_count)(&x, (QUEX_TYPE_CHARACTER*)TestString, (QUEX_TYPE_CHARACTER*)TestString + strlen(TestString));
    print(x, TestString);
}

void 
test_NoNewline(const char* TestString, QUEX_NAME(CounterLineColumnIndentation)& x)
{
    QUEX_NAME(CounterBase_shift_end_values_to_start_values)((QUEX_NAME(CounterBase)*)&x);
    QUEX_NAME(CounterLineColumnIndentation_count_NoNewline)(&x, (QUEX_TYPE_CHARACTER*)TestString, strlen(TestString));
    print(x, TestString);
}

void 
test_NoNewline_NeverStartOnWhitespace(const char* TestString, QUEX_NAME(CounterLineColumnIndentation)& x)
{
    int line_n = 0;
    for(const char* p=TestString; *p ; ++p) if( *p == '\n' ) ++line_n; 

    QUEX_NAME(CounterBase_shift_end_values_to_start_values)((QUEX_NAME(CounterBase)*)&x);
    QUEX_NAME(CounterLineColumnIndentation_count_NoNewline_NeverStartOnWhitespace)(&x, strlen(TestString));
    print(x, TestString);
}

void 
test_NoNewline_ContainsOnlySpace(const char* TestString, QUEX_NAME(CounterLineColumnIndentation)& x)
{
    int line_n = 0;
    for(const char* p=TestString; *p ; ++p) if( *p == '\n' ) ++line_n; 

    QUEX_NAME(CounterBase_shift_end_values_to_start_values)((QUEX_NAME(CounterBase)*)&x);
    QUEX_NAME(CounterLineColumnIndentation_count_NoNewline_ContainsOnlySpace)(&x, strlen(TestString));
    print(x, TestString);
}

int
main(int  argc, char** argv)
{
    my_tester                                y;
    QUEX_NAME(CounterLineColumnIndentation)  x;

    QUEX_NAME(CounterLineColumnIndentation_construct)(&x, &y);
    y.counter = (QUEX_NAME(CounterLineColumn)*)&x;
    x.base._line_number_at_end = 1;
        
    if( argc > 1 and string(argv[1]) == "--hwut-info" ) {
        cout << "Count Line and Column: With Indentation II\n";
        return 0;
    }

    // x.__buffer->__the_end = (QUEX_TYPE_CHARACTER*)0xFFFFFFFFL;

    // indentation[i] is going to be filled by: mini_mode::on_indentation(my_tester* x, int Indentation) 
    for(int i=0; i < 64; ++i) indentation[i] = 66;

    test("  [23", x);
    test("\n", x);
    test("\n   [bc", x);
    test_NoNewline_NeverStartOnWhitespace("[23   ", x);
    test("\n   ", x);
    test_NoNewline_ContainsOnlySpace("   ", x);
    test_NoNewline("   [YZ", x);
    test("\n   not\n   123", x);
    test("\n   not\n    ", x);
    test_NoNewline_NeverStartOnWhitespace("[bc", x);
    test("\nnot\n    ", x);
    test_NoNewline_NeverStartOnWhitespace("[BC", x);
    test("\n\n\n123    ", x);
    test("not\n\n\n  not   \n", x);
    test_NoNewline_NeverStartOnWhitespace("[234567890", x);

    cout << "## NOTE: Anything before the last newline inside a lexeme is ignored for indentation.\n";
    cout << "##       The following table may seem strange but it is well considered with respect\n";
    cout << "##       to this rule.\n";
    cout << "\n";
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
