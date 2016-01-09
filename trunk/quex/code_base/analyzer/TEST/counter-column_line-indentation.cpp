#include <my_tester.h>
#include <iostream>
#include <cstring>

using namespace std;
using namespace quex;


string    total_string;
int       indentation[64];
QUEX_NAME(Mode)  tester_mini_mode;

void
print(QUEX_NAME(CounterLineColumnIndentation)& x, const char* TestString)
{
    cout << "__________________________" << endl;
    // cout << "  before: " << x.base._line_number_at_begin << ", " << x.base._column_number_at_begin << endl;
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
    QUEX_NAME(CounterBase_shift_end_values_to_start_values)(&x.base);
    QUEX_NAME(CounterLineColumnIndentation_count)(&x, (QUEX_TYPE_LEXATOM*)TestString, 
                                  (QUEX_TYPE_LEXATOM*)TestString + strlen(TestString));
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
        cout << "Count Line and Column: With Indentation\n";
        return 0;
    }

    // x.__buffer->__the_end = (QUEX_TYPE_LEXATOM*)0xFFFFFFFFL;

    // indentation[i] is going to be filled by: mini_mode::on_indentation(my_tester* x, int Indentation) 
    for(int i=0; i < 64; ++i) indentation[i] = 66;

    test("  [23", x);
    test("\n", x);
    test("\n   [bc", x);
    test("[23   \n   ", x);
    test("   ", x);
    test("   [YZ", x);
    test("\n   [BC", x);
    test("\n   123", x);
    test("\n   [23", x);
    test("\n    ", x);
    test("[not\n", x);     // This shall not trigger an indentation event, because of the last '\n'
    test("not\n    ", x);
    test("[not\n\n", x);
    test("\n", x);
    test("123    ", x);
    test("[YZ\n\n\n  ", x);
    test("not   \n", x);
    test("[234567890", x);

    cout << "\n";
    cout << "## NOTE: Anything before the last newline inside a lexeme is ignored for indentation.\n";
    cout << "##       The following table may seem strange but it is well considered with respect\n";
    cout << "##       to this rule.\n";
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
