#include <my_tester.h>
#include <cstring>
#include <iostream>
#include <string>

using namespace std;

string total_string;

int    indentation[64];

void test(const char* TestString, my_tester& x)
{
    x._line_number_at_begin   = x._line_number_at_end;
    x._column_number_at_begin = x._column_number_at_end;
    x.count((QUEX_LEXEME_CHARACTER_TYPE*)TestString, strlen(TestString));
    

    cout << "__________________________" << endl;
    // cout << "  before: " << x.line_number_at_begin()    << ", " << x.column_number_at_begin() << endl;
    cout << "  lexeme: '";
    for(char* p = (char*)TestString; *p ; ++p) 
       if( *p == '\n' ) cout << "\\n";
       else             cout << *p;
    cout << "'" << endl;
    cout << "  after:  " << x.line_number_at_end()    << ", " << x.column_number_at_end() << endl;

    total_string += TestString;
}

int
main(int  argc, char** argv)
{
    my_tester   x;
        
    if( argc > 1 and strcmp(argv[1], "--hwut-info") == 0 ) {
        cout << "Count Line and Column: Without Indentation Count\n";
        return 0;
    }

    x.__buffer->__the_end = (QUEX_CHARACTER_TYPE*)0xFFFFFFFFL;

    test("12345", x);
    test("\n", x);
    test("\n12345", x);
    test("12345\n", x);
    test("123\n12345", x);
    test("\n12345\n12345", x);
    test("\n12345\n", x);
    test("12345\n12345\n", x);
    test("12345\n\n\n12345", x);
    test("12345\n\n\n12345\n", x);
    test("happy end", x);

    cout << "\n";
    cout << "Total String:\n";
    cout << "001: ";
    int line_n = 1;
    char tmp[6];
    for(int i = 0; i < total_string.length() ; ++i) {
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
