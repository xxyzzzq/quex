
#ifdef self_accumulator_add
/* Token / Token Policy _____________________________________________________*/
#   undef self_current_token_set_id
#   undef self_current_token_take_text

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
#endif

/* Token / Token Policy 
 * (NOTE: Macros for token sending are defined separately in file 'member/token-sending'.
 *        Those macros have to perform a little 'type loose').                            */
#define self_current_token_set_id(ID)            QUEX_TOKEN_POLICY_SET_ID(ID)
#define self_current_token_take_text(Begin, End) \
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

