#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__C_ADAPTIONS_H
#define __QUEX_INCLUDE_GUARD__ANALYZER__C_ADAPTIONS_H

#ifdef self_accumulator_add
/* Token / Token Policy _____________________________________________________*/
#   undef self_token_get_id
#   undef self_token_set_id
#   undef self_token_take_text

/* Modes ____________________________________________________________________*/
#   undef self_current_mode_p
#   undef self_current_mode_id
#   undef self_current_mode_name
/* Map: mode id to mode and vice versa */
#   undef self_map_mode_id_to_mode_p
#   undef self_map_mode_p_to_mode_id
/* Changing Modes */
#   undef self_set_mode_brutally
#   undef self_enter_mode
/* Changing Modes with stack */ 
#   undef self_pop_mode
#   undef self_pop_drop_mode
#   undef self_push_mode

/* Accumulator ______________________________________________________________*/
#   undef self_accumulator_add
#   undef self_accumulator_clear
#   undef self_accumulator_flush
/* Indentation/Counter _____________________________________________________*/
#   ifdef  QUEX_OPTION_LINE_NUMBER_COUNTING
#   undef  self_line_number            
#   undef  self_line_number_at_begin 
#   undef  self_line_number_at_end   
#   endif
#   ifdef  QUEX_OPTION_COLUMN_NUMBER_COUNTING
#   undef  self_column_number          
#   undef  self_column_number_at_begin 
#   undef  self_column_number_at_end   
#   endif
#   ifdef __QUEX_OPTION_INDENTATION_TRIGGER_SUPPORT
#   undef self_indentation                    
#   undef self_disable_next_indentation_event 
#   endif
#endif

/* Token / Token Policy 
 * (NOTE: Macros for token sending are defined separately in file 'member/token-sending'.
 *        Those macros have to perform a little 'type loose').                            */
#if        defined(__QUEX_OPTION_PLAIN_C)
#   define self_token_get_id(ID)    __QUEX_CURRENT_TOKEN_P->_id
#else
#   define self_token_get_id(ID)    __QUEX_CURRENT_TOKEN_P->type_id()
#endif
#define self_token_set_id(ID)    QUEX_TOKEN_POLICY_SET_ID(ID)
#define self_token_take_text(Begin, End) \
        QUEX_NAME_TOKEN(take_text)(__QUEX_CURRENT_TOKEN_P, &self, (Begin), (End))

/* Modes */
#define self_current_mode_p()     /* QUEX_NAME(Mode)* */ QUEX_NAME(mode)(&self)
#define self_current_mode_id()    /* int */              QUEX_NAME(mode_id)(&self)
#define self_current_mode_name()  /* const char* */      QUEX_NAME(mode_name)(&self)

/* Map: mode id to mode and vice versa */
#define self_map_mode_id_to_mode_p(ID)    QUEX_NAME(map_mode_id_to_mode)(&self, (ID))
#define self_map_mode_p_to_mode_id(ModeP) QUEX_NAME(map_mode_to_mode_id)(&self, (ModeP))

/* Changing Modes */
#define self_set_mode_brutally(ModeP)     QUEX_NAME(set_mode_brutally)(&self, (ModeP))
#define self_enter_mode(ModeP)            QUEX_NAME(enter_mode)(&self, (ModeP))

/* Changing Modes with stack */ 
#define self_pop_mode()                   QUEX_NAME(pop_mode)(&self)
#define self_pop_drop_mode()              QUEX_NAME(pop_drop_mode)(&self)
#define self_push_mode()                  QUEX_NAME(push_mode)(&self, (NewModeP))

#define self_accumulator_clear()                     QUEX_NAME(Accumulator_clear)(&self.accumulator)
#define self_accumulator_flush(TOKEN_ID)             QUEX_NAME(Accumulator_flush)(&self.accumulator, \
                                                                                  TOKEN_ID)
#define self_accumulator_add(LexemeBegin, LexemeEnd) QUEX_NAME(Accumulator_add)(&self.accumulator, \
                                                               (LexemeBegin), (LexemeEnd))
#ifdef      QUEX_OPTION_LINE_NUMBER_COUNTING
#   define  self_line_number_at_begin()   (self.counter.base._line_number_at_begin)
#   define  self_line_number_at_end()     (self.counter.base._line_number_at_end)
#   define  self_line_number()            (self_line_number_at_begin())
#endif
#ifdef      QUEX_OPTION_COLUMN_NUMBER_COUNTING
#   define  self_column_number_at_begin() (self.counter.base._column_number_at_begin)
#   define  self_column_number_at_end()   (self.counter.base._column_number_at_end)
#   define  self_column_number()          (self_column_number_at_begin())
#endif
#ifdef      __QUEX_OPTION_INDENTATION_TRIGGER_SUPPORT
#   define  self_indentation()                    (self.counter._indentation)
#   define  self_disable_next_indentation_event() (self.counter._indentation_event_enabled_f = false)
#endif

#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__C_ADAPTIONS_H */
