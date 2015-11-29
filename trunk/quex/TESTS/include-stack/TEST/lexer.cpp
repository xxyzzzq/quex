#include<fstream>    
#include<iostream> 

// (*) include lexical analyser header
#include "Simple"
#include "Simple-token_ids"

using namespace std;

QUEX_TYPE_CHARACTER  EmptyLexeme = 0x0000;  /* Only the terminating zero */

void    print(quex::Simple& qlex, quex::Token& Token, bool TextF = false);
void    print(quex::Simple& qlex, const char* Str1, const char* Str2=0x0, const char* Str3=0x0);

#if 0 && QUEX_OPTION_TOKEN_POLICY_USERS_QUEUE
//     Policy 'users_queue' has been deprecated.
//     void get_token_from_users_queue(quex::Simple&, quex::Token&);
//#    define RECEIVE(Token)   get_token_from_users_queue(qlex, Token)
#endif
#ifdef  QUEX_OPTION_TOKEN_POLICY_QUEUE
#    define RECEIVE(TokenP)   (void)qlex.receive(&TokenP)
#else
#    define RECEIVE(TokenP)   (void)qlex.receive()
#endif

static void
self_test(const char* CharFilename);

int 
main(int argc, char** argv) 
{        
    if( argc < 2 ) {
        printf("Need at least one argument.\n");
        return -1;
    }
    else if( strcmp(argv[1], "--hwut-info") == 0 ) {
        printf("Include Stack: Misc Scenarios;\n");
        printf("CHOICES: empty, 1, 2, 3, 4, 5, 20;");
        return 0;
    }

    self_test(argv[1]);
}

static void
self_test(const char* CharFilename)
{
    string         Directory("example/");
    string         Filename(CharFilename);
    ifstream       istr((Directory + Filename + ".txt").c_str());
    quex::Simple   qlex(&istr);

#   ifdef  QUEX_OPTION_TOKEN_POLICY_QUEUE
    quex::Token*  token_p = 0x0;
#   else
    quex::Token*  token_p = qlex.token_p();
#   endif


    qlex.input_name = (Directory + Filename + ".txt").c_str();
    cout << "[START]\n";

    do {
        RECEIVE(token_p);

        print(qlex, *token_p, true);

    } while( token_p->type_id() != QUEX_TKN_TERMINATION );

    cout << "[END]\n";
}

string  space(int N)
{ string tmp; for(int i=0; i<N; ++i) tmp += "    "; return tmp; }

void  print(quex::Simple& qlex, quex::Token& Token, bool TextF /* = false */)
{ 
    cout << space(qlex.include_depth) << Token.line_number() << ": (" << Token.column_number() << ")";
    cout << Token.type_id_name();
    if( TextF ) cout << "\t'" << Token.get_text().c_str() << "'";
    cout << endl;
}

void print(quex::Simple& qlex, const char* Str1, const char* Str2 /* = 0x0 */, const char* Str3 /* = 0x0*/)
{
    cout << space(qlex.include_depth) << Str1;
    if( Str2 != 0x0 ) cout << Str2;
    if( Str3 != 0x0 ) cout << Str3;
    cout << endl;
}

#if 0 && QUEX_OPTION_TOKEN_POLICY_USERS_QUEUE
// Policy 'users_queue' deprecated.
void get_token_from_users_queue(quex::Simple& qlex, quex::Token& Token)
{
    static quex::Token   Begin[3];
    static quex::Token*  End  = Begin + 3;
    
    if( QUEX_NAME(TokenQueue_is_empty)(&qlex._token_queue) ) {
        qlex.receive(Begin, End);
    }
    Token = *qlex._token_queue.read_iterator++;
}
#endif
