// -*- C++ -*- vim:set syntax=cpp:
#ifndef __INCLUDE_GUARD__QUEX__INCLUDE_STACK_I__
#define __INCLUDE_GUARD__QUEX__INCLUDE_STACK_I__

#include <quex/code_base/template/Analyser>
namespace quex { 

    template <class InputHandleT> inline void    
    CLASS::include_push(QUEX_TYPE_CHARACTER*     InputName,
                        const QuexMode&          mode, 
                        const char*              IANA_CodingName /* = 0x0 */)
    {
        // Once we allow MODE_ID == 0, reset the range to [0:MAX_MODE_CLASS_N]
        include_push<InputHandleT>(InputName, mode.id(), IANA_CodingName);
    }

    template <class InputHandleT> inline void    
    CLASS::include_push(QUEX_TYPE_CHARACTER*     InputName,
                        const int                MODE_ID /* = -1 */, 
                        const char*              IANA_CodingName /* = 0x0 */)
    {
        // Once we allow MODE_ID == 0, reset the range to [0:MAX_MODE_CLASS_N]
        __quex_assert(    MODE_ID == -1 
                      || (MODE_ID >= 1 && MODE_ID < __QUEX_SETTING_MAX_MODE_CLASS_N + 1));
        // IANA_CodingName == 0x0 possible if normal ASCII is ment (e.g. no iconv support)

        /* Store the lexical analyser's to the state before the including */
        /* Here, the 'memento_pack' section is executed                   */
        InputHandleT*   input_handle = 0x0;
        CLASS_MEMENTO*  m            = memento_pack(InputName, &input_handle);
        if( m == 0x0 ) return;
        if( input_handle == 0x0 ) {
            QUEX_ERROR_EXIT("Segment 'memento_pack' segment did not set the input_handle.");
        }

        if( MODE_ID != -1 ) this->set_mode_brutally(MODE_ID);

        /* Initialize the lexical analyzer for the new input stream.             */
        /* Include stacks cannot be used with plain direct user memory => 0x0, 0 */
        this->__init(input_handle, IANA_CodingName, 0x0, 0);

        /* Keep track of 'who's your daddy?'                              */
        m->parent = this->_parent_memento;
        this->_parent_memento = m;
    }   

    inline bool
    CLASS::include_pop() 
    {
        /* Not included? return 'false' to indicate we're on the top level     */
        if( this->_parent_memento == 0x0 ) return false; 

        /* (1) Free the related memory that is no longer used                  */
        QuexAnalyser_destruct((QuexAnalyser*)this);

        /* Restore the lexical analyser to the state it was before the include */
        /* Here, the 'memento_unpack' section is executed                      */
        memento_unpack(this->_parent_memento);

        /* Return to including file succesful */
        return true;
    }

} // namespace quex

#endif // __INCLUDE_GUARD__QUEX__INCLUDE_STACK_I__
