// -*- C++ -*- vim:set syntax=cpp:

#ifdef QUEX_OPTION_DEBUG_TOKEN_SENDING
#   define __QUEX_DEBUG_TOKEN_SENDING() \
        std::cerr << "$$LEXER_CLASS_NAME$$::send " << _token << std::endl;
#else
#   define __QUEX_DEBUG_TOKEN_SENDING() /* nothing */
#endif

inline void   
CLASS::send(const __QUEX_SETTING_TOKEN_CLASS_NAME& That) 
{
    _token = That;
    __QUEX_DEBUG_TOKEN_SENDING();
}

inline void   
CLASS::send(const __QUEX_SETTING_TOKEN_CLASS_NAME::id_type ID) 
{
    _token.set(ID);
    __QUEX_DEBUG_TOKEN_SENDING();
}

inline void   
CLASS::send_n(const int N, __QUEX_SETTING_TOKEN_CLASS_NAME::id_type ID) 
{
    /* this function does not make sense for singleton tokens */
    _token.set(ID); // applies DEBUG of 'send()'
    __QUEX_DEBUG_TOKEN_SENDING();
}

template <typename ContentT>
inline void   
CLASS::send(const __QUEX_SETTING_TOKEN_CLASS_NAME::id_type ID, ContentT Content) 
{
    _token.set(ID, Content);
    __QUEX_DEBUG_TOKEN_SENDING();
}

#undef __QUEX_DEBUG_TOKEN_SENDING


