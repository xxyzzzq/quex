#ifndef __TOKEN_H__
#define __TOKEN_H__

#ifndef    QUEX_TYPE_TOKEN_ID
#   define QUEX_TYPE_TOKEN_ID              uint32_t
#endif

typedef struct Token_tag {
    QUEX_TYPE_TOKEN_ID    _id;

    size_t _line_n;
    size_t _column_n;
} Token;

extern void QUEX_NAME_TOKEN(copy)(Token* me, const Token* Other);
extern void QUEX_NAME_TOKEN(construct)(Token* __this);
extern void QUEX_NAME_TOKEN(destruct)(Token* __this);



#endif

 	  	 
