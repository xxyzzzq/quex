#include<iostream> 
#include<cstring> 

#include "EasyLexer"

void test(size_t Size0, size_t ContentSize0, size_t Size1, size_t ContentSize1);

int 
main(int argc, char** argv) 
{        
    test(77, 60, 66, 50);
    test(77, 0,  66, 50);
    test(0,  0,  66, 50);
    test(77, 60, 66, 0);
    test(77, 0,  66, 0);
    test(0,  0,  66, 0);
    test(77, 60,  0, 0);
    test(77, 0,   0, 0);
    test(0,  0,   0, 0);

    return 0;
}

void test(size_t Size0, size_t ContentSize0, size_t Size1, size_t ContentSize1)
{
    using namespace std;

    QUEX_TYPE_CHARACTER*  buffer_0 = (Size0 == 0) ? 0x0 : new QUEX_TYPE_CHARACTER[Size0];
    QUEX_TYPE_CHARACTER*  buffer_1 = (Size1 == 0) ? 0x0 : new QUEX_TYPE_CHARACTER[Size1];

    memset(buffer_0, 'a', Size0);
    memset(buffer_1, 'b', Size1);

    quex::EasyLexer qlex((QUEX_TYPE_CHARACTER*)buffer_0, Size0, buffer_0 + ContentSize0 + 1); 

    cout << "--------------------------------------------------------------------------\n";
    cout << "Constructor:\n";
    cout << "   (Size0 = " << Size0 << ", ContentSize0 = " << ContentSize0 << ")\n";
    cout << "   size       = " << (qlex.buffer._memory._back + 1      - qlex.buffer._memory._front) << endl;
    cout << "   eof offset = " << (qlex.buffer.input.end_p - qlex.buffer._memory._front) << endl;

    QUEX_TYPE_CHARACTER*  prev = qlex.reset(buffer_1, Size1, buffer_1 + ContentSize1 + 1);
    if( prev != 0x0 ) delete [] prev;

    cout << "\n\n";
    cout << "reset_buffer reported buffer: " << ((prev == buffer_0) ? "Correct" : "False");
    if( prev != buffer_0 ) cout << "\n## " << (long)prev << " " << (long)buffer_0 << endl;
    cout << "\n\n";

    cout << "'reset_buffer':\n";
    cout << "   (Size1 = " << Size1 << ", ContentSize1 = " << ContentSize1 << ")\n";
    cout << "   size       = " << (qlex.buffer._memory._back + 1      - qlex.buffer._memory._front) << endl;
    cout << "   eof offset = " << (qlex.buffer.input.end_p - qlex.buffer._memory._front) << endl;

    if( buffer_1 != 0x0 ) {
        prev = qlex.reset(0x0, 0, 0x0);
        cout << "\n\n";
        cout << "reset_buffer reported buffer: " << ((prev == buffer_1) ? "Correct" : "False");
        if( prev != buffer_1 ) cout << "\n## " << (long)prev << " " << (long)buffer_1 << endl;
        cout << "\n\n";
        
        if( prev != 0x0 ) delete [] prev;
    }
}

