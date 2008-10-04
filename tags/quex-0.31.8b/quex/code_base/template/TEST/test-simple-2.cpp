#include <my_tester.h>
#include <iostream>
#include <string>

using namespace std;


string total_string;
int    indentation[64];

void test(const char* TestString, my_tester& x)
{
    x._line_number_at_begin   = x._line_number_at_end;
    x._column_number_at_begin = x._column_number_at_end;

    cout << "__________________________" << endl;

    // cout << "  before: " << x.line_number_at_begin()    << ", " << x.column_number_at_begin() << endl;
    cout << "  lexeme: '";
    for(char* p = (char*)TestString; *p ; ++p) 
       if( *p == '\n' ) cout << "\\n";
       else             cout << *p;
    cout << "'" << endl;
    x.count_indentation((QUEX_CHARACTER_TYPE*)TestString, strlen(TestString));
    cout << "  end:    " << x.line_number_at_end()    << ", " << x.column_number_at_end() << endl;

    total_string += TestString;
}

int
main(int  argc, char** argv)
{
    my_tester   x;
        
    if( argc > 1 and string(argv[1]) == "--hwut-info" ) {
        cout << "Count Line and Column: With Indentation\n";
        return 0;
    }

    x.__buffer->__the_end = (QUEX_CHARACTER_TYPE*)0xFFFFFFFFL;

    for(int i=0; i < 64; ++i) indentation[i] = 66;

    test("  [23", x);
    test("\n", x);
    test("\n   [bc", x);
    test("[23   \n   ", x);
    test("   ", x);
    test("   [YZ", x);
    test("\n   [BC\n   123", x);
    test("\n   [23\n    ", x);
    test("[bc\n123\n    ", x);
    test("[BC\n\n\n123    ", x);
    test("[YZ\n\n\n  123   \n", x);
    test("[234567890", x);

    cout << "\n";
    cout << "Total String:\n";
    cout << "001: [" << indentation[0] << "] ";
    int line_n = 1;
    char tmp[6];
    for(int i = 0; i < total_string.length() ; ++i) {
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
