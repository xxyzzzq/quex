/* Lexical Analyzer fed from a Command Line
 * -----------------------------------------
 *
 * In this example, user interaction results in a command line which is then
 * lexically analyzed. This example requires the 'GNU readline' library to
 * be installed.
 *_____________________________________________________________________________
 *
 *  EXAMPLE:
 *  
 *    Ascii-codec command line:
 *
 *          > ./lexer-command-line
 *        
 *          type here: A message of a kilobyte
 *              read: 24 [byte]
 *              Token: ARTICLE 'A'
 *              Token: SUBJECT 'message'
 *              Token: PREPOSITION 'of'
 *              Token: ARTICLE 'a'
 *              Token: SUBJECT 'kilobyte'
 *              Token: <TERMINATION> ''
 *          type here: starts with a single bit
 *              read: 25 [byte]
 *              Token: SUBJECT 'starts'
 *              Token: PREPOSITION 'with'
 *              Token: ARTICLE 'a'
 *              Token: ATTRIBUTE 'single'
 *              Token: STORAGE_UNIT 'bit'
 *              Token: <TERMINATION> ''
 *          type here: ^C
 *        
 *    Similarly, the UTF8 command line parser may be used:
 *        
 *          > ./lexer-command-line-utf8
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
    Token*                   token;
    LEXER_CLASS*             qlex;   
    size_t                   size = 4096;
    char                     buffer[4096];
    char*                    p;
    ssize_t                  received_n;
    QUEX_NAME(BufferFiller)* filler = QUEX_NAME(BufferFiller_new_DEFAULT)(NULL, CODEC);

    qlex = new LEXER_CLASS(filler);

    while( 1 + 1 == 2 ) {
        printf("type here: ");
        p    = &buffer[0];
        size = 4096;
        if( (received_n = getline(&p, &size, stdin)) == -1 ) break;

        printf("    read: %i [byte]\n", received_n);
        qlex->reset();
        qlex->buffer.fill(&qlex->buffer, &p[0], &p[received_n]);

        token = qlex->token;
        do {
            qlex->receive();
            printf("   Token: %s\n", token->get_string().c_str()); 
        } while( token->_id != QUEX_TKN_TERMINATION && token->_id != QUEX_TKN_BYE );
    }
        
    delete qlex; 
    filler->delete_self(filler);
    printf("<terminated>\n");
    return 0;
}


