#ifndef __TOKEN_H__
#define __TOKEN_H__

#ifndef    QUEX_TYPE_TOKEN_ID
#   define QUEX_TYPE_TOKEN_ID              uint32_t
#endif

typedef struct quex_Token_tag {
    QUEX_TYPE_TOKEN_ID    _id;

    size_t _line_n;
    size_t _column_n;
} quex_Token;

extern void QUEX_NAME_TOKEN(copy)(quex_Token* me, const quex_Token* Other);
extern void QUEX_NAME_TOKEN(construct)(quex_Token* __this);
extern void QUEX_NAME_TOKEN(destruct)(quex_Token* __this);



#endif

 	  	 
