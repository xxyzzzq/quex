#include<fstream>    
#include<iostream> 
#include<sstream> 

#include "tiny_lexer"

size_t messaging_framework_receive(uint8_t** buffer);
void   messaging_framework_release(uint8_t* buffer);

int 
main(int argc, char** argv) 
{        
    using namespace std;

    // (*) create token
    quex::Token           token;
    // (*) create the lexical analyser
    quex::tiny_lexer      qlex;
    QUEX_TYPE_CHARACTER*  msg         = 0x0;
    QUEX_TYPE_CHARACTER*  chunk_begin = 0x0;
    QUEX_TYPE_CHARACTER*  chunk_end   = chunk_begin;
    size_t                chunk_size  = 0;

    while( 1 + 1 == 2 ) {
        // -- Receive content from a messaging framework
        if( chunk_begin == chunk_end ) {
            if( msg != 0x0 ) messaging_framework_release(msg);
            chunk_size  = messaging_framework_receive(&msg);
            chunk_begin = msg;
            chunk_end   = chunk_begin + chunk_size;
        } else {
            // If chunk_begin != chunk_end, this means that there are still
            // some characters in the pipeline. Let us use them first.
        }

        // -- Copy buffer content into the analyzer's buffer
        chunk_begin = qlex.buffer_fill_region_append(chunk_begin, chunk_end);

        // -- Loop until the 'termination' token arrives
        do {
            qlex.receive(&token);
            cout << string(token) << endl;
        } while( token.type_id() != QUEX_TKN_TERMINATION && token.type_id() != QUEX_TKN_BYE );

        if( token.type_id() == QUEX_TKN_BYE ) break;
    }

    return 0;
}

size_t 
messaging_framework_receive(uint8_t** buffer)
{
    static char   data[] = "hello 4711 bonjour 0815 world 7777 le 31451 monde 00 welt 1234567890 hallo 1212 hello bye";
    const size_t  L = sizeof(data) / sizeof(char);
    char*         iterator = data;
    size_t        size = random() * 5 + 1;

    assert(iterator < data + L);
    if( iterator + size >= data + L ) size = L - (iterator - data); 

    *buffer = (uint8_t*)malloc(size * sizeof(uint8_t));
    
    memcpy(buffer, iterator, size);

    iterator += size;

    return size;
}

void 
messaging_framework_release(uint8_t* buffer)
{
    free((void*)buffer);
}
