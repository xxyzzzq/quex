/* -*- C++ -*- vim: set syntax=cpp:
 * PURPOSE: File containing definition of token-identifier and
 *          a function that maps token identifiers to a string
 *          name.
 *
 * NOTE: This file has been created automatically by Quex.
 *       Visit quex.org for further info.
 *
 * DATE: Sun Feb 10 08:45:02 2013
 *
 * (C) 2005-2010 Frank-Rene Schaefer
 * ABSOLUTELY NO WARRANTY                                           */
#ifndef __QUEX_INCLUDE_GUARD__AUTO_TOKEN_IDS_QUEX_COMMON__COMMON_TOKEN__
#define __QUEX_INCLUDE_GUARD__AUTO_TOKEN_IDS_QUEX_COMMON__COMMON_TOKEN__

#ifndef __QUEX_OPTION_PLAIN_C
#   include<cstdio> 
#else
#   include<stdio.h> 
#endif

/* The token class definition file can only be included after 
 * the definition on TERMINATION and UNINITIALIZED.          
 * (fschaef 12y03m24d: "I do not rememember why I wrote this.
 *  Just leave it there until I am clear if it can be deleted.")   */
#include "Common-token.h"

#define TKN_ADVERB____    ((QUEX_TYPE_TOKEN_ID)10000)
#define TKN_ARTICLE___    ((QUEX_TYPE_TOKEN_ID)10001)
#define TKN_DEDENT        ((QUEX_TYPE_TOKEN_ID)3)
#define TKN_FILL_WORD_    ((QUEX_TYPE_TOKEN_ID)10002)
#define TKN_INDENT        ((QUEX_TYPE_TOKEN_ID)2)
#define TKN_MARK______    ((QUEX_TYPE_TOKEN_ID)10003)
#define TKN_ME________    ((QUEX_TYPE_TOKEN_ID)10004)
#define TKN_MY_BROTHER    ((QUEX_TYPE_TOKEN_ID)10005)
#define TKN_NEGATION__    ((QUEX_TYPE_TOKEN_ID)10006)
#define TKN_NODENT        ((QUEX_TYPE_TOKEN_ID)4)
#define TKN_OK            ((QUEX_TYPE_TOKEN_ID)10007)
#define TKN_PREDICATE_    ((QUEX_TYPE_TOKEN_ID)10008)
#define TKN_SCALLYWAG_    ((QUEX_TYPE_TOKEN_ID)10009)
#define TKN_SUBJECT___    ((QUEX_TYPE_TOKEN_ID)10010)
#define TKN_TERMINATION   ((QUEX_TYPE_TOKEN_ID)0)
#define TKN_UKNOWN____    ((QUEX_TYPE_TOKEN_ID)10011)
#define TKN_UNINITIALIZED ((QUEX_TYPE_TOKEN_ID)1)
#define TKN_VERB______    ((QUEX_TYPE_TOKEN_ID)10012)


QUEX_NAMESPACE_TOKEN_OPEN
extern const char* QUEX_NAME_TOKEN(map_id_to_name)(const QUEX_TYPE_TOKEN_ID TokenID);
QUEX_NAMESPACE_TOKEN_CLOSE

#endif /* __QUEX_INCLUDE_GUARD__AUTO_TOKEN_IDS_QUEX_COMMON__COMMON_TOKEN__ */
