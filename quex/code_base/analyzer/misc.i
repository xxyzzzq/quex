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


    inline void
    CLASS::print_this()
    {
        __QUEX_STD_printf("   CurrentMode = %s;\n", __current_mode_p == 0x0 ? "0x0" : __current_mode_p->name);

        QuexBuffer_print_this(&this->buffer);

#       ifdef QUEX_OPTION_STRING_ACCUMULATOR
        accumulator.print_this();
#       endif
        counter.print_this(&counter);
#       ifdef QUEX_OPTION_POST_CATEGORIZER
        post_categorizer.print_this();
#       endif
        __QUEX_STD_printf("   Mode Stack (%i/%i) = [", 
                          (int)(_mode_stack.end        - _mode_stack.begin),
                          (int)(_mode_stack.memory_end - _mode_stack.begin));
        for(CLASS_QUEX_MODE** iterator=_mode_stack.end-1; iterator >= _mode_stack.begin; --iterator)
            __QUEX_STD_printf("%s, ", (*iterator)->name);

        __QUEX_STD_printf("]\n");
        __QUEX_STD_printf("   ByteOrderInversion = %s;\n", byte_order_reversion() ? "true" : "false");
    }

} // namespace quex
