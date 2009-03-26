// -*- C++ -*- vim:set syntax=cpp:
#ifndef __INCLUDE_GUARD__QUEX__INCLUDE_STACK_I__
#define __INCLUDE_GUARD__QUEX__INCLUDE_STACK_I__

#include <quex/code_base/template/Analyser>
namespace quex { 

    template <class InputHandle> inline void    
    CLASS::include_push(InputHandle*             new_input_handle_p, 
                        const QuexMode&          mode, 
                        QuexBufferFillerTypeEnum BFT /* = QUEX_AUTO */,
                        const char*              IANA_CodingName /* = 0x0 */)
    {
        // Once we allow MODE_ID == 0, reset the range to [0:MAX_MODE_CLASS_N]
        __push(new_input_handle_p, mode.analyser_function, IANA_CodingName);
    }

    template <class InputHandle> inline void    
    CLASS::include_push(InputHandle*            new_input_handle_p, 
                       const int                MODE_ID /* = -1 */, 
                       QuexBufferFillerTypeEnum BFT /* QUEX_AUTO */,
                       const char*              IANA_CodingName /* = 0x0 */)
    {
        // Once we allow MODE_ID == 0, reset the range to [0:MAX_MODE_CLASS_N]
        __quex_assert(    MODE_ID == -1 
                      || (MODE_ID >= 1 && MODE_ID < __QUEX_SETTING_MAX_MODE_CLASS_N + 1));
        __quex_assert(new_input_handle_p != 0x0);
        // IANA_CodingName == 0x0 possible if normal ASCII is ment (e.g. no iconv support)

        CLASS_MEMENTO*  m = QUEX_NAMER(CLASS_MEMENTO, _pack,)(this);

        if( MODE_ID != -1 ) this->set_mode_brutally(MODE_ID);

        /* Initialize the lexical analyzer for the new input stream */
        this->__init(new_input_handle_p, BFT, IANA_CodingName);

        /* Keep track of 'who's your daddy?' */
        m->parent = this->_parent_memento;
        this->_parent_memento = m;
    }   

    inline bool
    CLASS::include_pop() 
    {
        /* Not included? return 'false' to indicate we're on the top level */
        if( this->_parent_memento == 0x0 ) return false; 

        // (1) Free the related memory that is no longer used
        QuexAnalyser_destruct((QuexAnalyser*)this);

        /* Reset the lexical analyser to the state it was before the include */
        QUEX_NAMER(CLASS_MEMENTO, _unpack,)(this->_parent_memento, this);

        /* Return to including file succesful */
        return true;
    }

} // namespace quex

#endif // __INCLUDE_GUARD__QUEX__INCLUDE_STACK_I__
