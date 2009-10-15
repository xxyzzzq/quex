#include <my_tester.h>
#include <cstring>
#include <cstdio>

using namespace std;
using namespace quex;

char total_string[65536];

int    indentation[64];

void test(const char* TestString, CounterLineColumn& x)
{
    x.base._line_number_at_begin   = x.base._line_number_at_end;
    x.base._column_number_at_begin = x.base._column_number_at_end;
    CounterLineColumn_count(&x, (QUEX_TYPE_CHARACTER*)TestString, (QUEX_TYPE_CHARACTER*)TestString + strlen(TestString));

    printf("__________________________\n");
    printf("  lexeme: '");
    for(char* p = (char*)TestString; *p ; ++p) 
       if( *p == '\n' ) printf("\\n");
       else             printf("%c", *p);
    printf("'\n");
    printf("  after:  %i, %i\n", 
           (int)x.base._line_number_at_end, (int)x.base._column_number_at_end);

    strcat(total_string, TestString);
}

int
main(int  argc, char** argv)
{
    CounterLineColumn   x;
    CounterLineColumn_construct(&x, 0x0 /* second arg only for conformity with other counter */);
        
    if( argc > 1 and strcmp(argv[1], "--hwut-info") == 0 ) {
        printf("Count Line and Column: Without Indentation Count\n");
        return 0;
    }

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

    printf("\n");
    printf("Total String:\n");
    printf("001: ");
    int line_n = 1;
    for(size_t i = 0; i < strlen(total_string) ; ++i) {
        if( total_string[i] == '\n' ) {
            ++line_n;
            printf("\n%03i: ", (int)line_n); 
        } else {
            printf("%c", (char)total_string[i]);
        }
    }
    printf("\n");
}
