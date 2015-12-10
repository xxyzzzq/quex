#ifndef __INCLUDE_GUARD_PARSER_H__
#define __INCLUDE_GUARD_PARSER_H__

/* Enabling traces.  */
#ifndef YYDEBUG
# define YYDEBUG 0
#endif

/* Enabling verbose error messages.  */
#ifdef YYERROR_VERBOSE
# undef YYERROR_VERBOSE
# define YYERROR_VERBOSE 1
#else
# define YYERROR_VERBOSE 0
#endif

/* Enabling the token table.  */
#ifndef YYTOKEN_TABLE
# define YYTOKEN_TABLE 0
#endif


namespace Example {

    class BisonParser
    {
    public:
#ifndef YYSTYPE
        typedef int semantic_type;
#else
        typedef YYSTYPE semantic_type;
#endif
        static const int NOT_CONSIDERED0 = 0;
        enum { 
            NOT_CONSIDERED1 = 0
        };
        struct token
        {
            /* Tokens.  */
            enum yytokentype {
                TK_INTEGER = 258
            };

            static const int NOT_CONSIDERED2 = 0;
        };
        static const int NOT_CONSIDERED3 = 0;
        enum { 
            NOT_CONSIDERED4 = 0
        };
        typedef token::yytokentype token_type;

        BisonParser();
        virtual ~BisonParser ();

        virtual int parse ();
    };
    const int NOT_CONSIDERED2 = 0;
}

#endif /* ! defined __INCLUDE_GUARD_PARSER_H__ */
