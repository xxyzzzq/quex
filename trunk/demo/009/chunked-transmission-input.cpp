#include<fstream>    
#include<iostream> 
#include<sstream> 

#include <./tiny_lexer>

size_t receive_transmission(uint8_t* buffer, size_t BufferSize);

int 
main(int argc, char** argv) 
{        
    using namespace std;

    // (*) create token
    quex::Token        Token;
    // (*) create the lexical analyser
    //     if no command line argument is specified user file 'example.txt'
    quex::tiny_lexer   qlex = new quex::tiny_lexer();

    cout << ",------------------------------------------------------------------------------------\n";

    while( 1 + 1 == 2 ) {
        qlex.buffer_prepare_append();

        int count_n = receive_transmission(qlex.buffer_text_end(), qlex.buffer_remaining_free_space());
        qlex.buffer_appended(count_n);

        cout << "[[Received " << count_n << " characters in chunk.]]\n";
        
        // Loop until the 'termination' token arrives
        do {
            qlex.receive(&Token);
            cout << string(Token) << endl;
        } while( Token.type_id() != QUEX_TKN_TERMINATION && Token.type_id() != QUEX_TKN_BYE );
        
        if( Token.type_id() == QUEX_TKN_BYE ) break;
    }

    cout << "`------------------------------------------------------------------------------------\n";

    return 0;
}

size_t receive_transmission(uint8_t* buffer, size_t BufferSize)
{
    static char   data[] = "hello 4711 bonjour 0815 world 7777 le 31451 monde 00 welt 1234567890 hallo 1212 hello bye";
    const size_t  L = sizeof(data) / sizeof(char);
    char*         iterator = data;
    size_t        RandomSize = random() * 5;
    char*         ChunkSize = RandomSize > BufferSize ? BufferSize : RandomSize;
    memcpy(buffer, data, ChunkSize);

    return ChunkSize;
}
