/* Stdandard-Input-Based Lexical Analyzer
 * --------------------------------------
 *
 * This application implements a lexical analyzer that reads from the Standard
 * Input, often referred to as 'stdin'. It does so by means of a POSIX byte
 * loader (while a FILE byte loader may equally do). The lexical analysis
 * terminates with the termination character on the standard input 'Ctrl-D'.
 *_____________________________________________________________________________
 *
 * EXAMPLE:
 *
 *  Under Unix/Linux use the 'pipe' character to redirect the output of a 
 *  command to the standard input of the lexical analyzer.
 *  
 *     > cat example-feed.txt | ./lexer-stdin
 *
 *  Or, respectively for a UTF8 lexer:
 *
 *     > cat example-feed-utf8.txt | ./lexer-stdin-utf8
 *  
 *_____________________________________________________________________________
 *
 * (C) Frank-Rene Schaefer                                                   */

#include <stdio.h>
#if ! defined(WITH_UTF8)
#   include <LexAscii>
#   define  LEXER_CLASS   LexAscii
#   define  CODEC         NULL
#else
#   include <LexUtf8>
#   define  LEXER_CLASS   LexUtf8
#   define  CODEC         "UTF8"
#endif

int 
main(int argc, char** argv) 
{        
    using namespace quex;

    Token*                 token;
    LEXER_CLASS*           qlex;   
    QUEX_NAME(ByteLoader)* loader = QUEX_NAME(ByteLoader_POSIX_new)(0); /* 0 = stdin */

    QUEX_NAME(ByteLoader_seek_disable)(loader);

    qlex = new LEXER_CLASS(loader, CODEC);

    token = qlex->token;
    do {
        qlex->receive(); 
        printf("   Token: %s\n", token->get_string().c_str()); 
    } while( token->_id != QUEX_TKN_TERMINATION && token->_id != QUEX_TKN_BYE );
        
    delete qlex;
    loader->delete_self(loader);
    return 0;
}


