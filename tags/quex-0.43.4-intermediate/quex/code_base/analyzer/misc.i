/* -*- C++ -*-   vim: set syntax=cpp:
 *
 * No include guards, the header might be included from multiple lexers.
 *
 * NOT: #ifndef __INCLUDE_GUARD__QUEX_LEXER_CLASS_MISC_I__
 * NOT: #define __INCLUDE_GUARD__QUEX_LEXER_CLASS_MISC_I__       */

namespace quex { 
    inline void    
    CLASS::move_forward(const size_t CharacterN)
    {
        QuexBuffer_move_forward(&this->buffer, CharacterN);
    }

    inline void    
    CLASS::move_backward(const size_t CharacterN)
    {
        QuexBuffer_move_backward(&this->buffer, CharacterN);
    }

    
    inline size_t  
    CLASS::tell()
    {
        return QuexBuffer_tell(&this->buffer);
    }

    inline void    
    CLASS::seek(const size_t CharacterIndex)
    {
        QuexBuffer_seek(&this->buffer, CharacterIndex);
    }

} // namespace quex
