/* -*- C++ -*-  vim:set syntax=cpp: 
 *
 * (C) 2004-2010 Frank-Rene Schaefer
 * ABSOLUTELY NO WARRANTY              */
#ifndef __QUEX_INCLUDE_GUARD__ANALYZER__MODE_I
#define __QUEX_INCLUDE_GUARD__ANALYZER__MODE_I

    QUEX_INLINE void
    QUEX_NAME(Mode_uncallable_analyzer_function)(QUEX_TYPE_ANALYZER* me)
    { __quex_assert(0); return; }

    QUEX_INLINE void
    QUEX_NAME(Mode_on_indentation_null_function)(QUEX_TYPE_ANALYZER* me, 
                                                 const int  Indentation) 
    { }

    QUEX_INLINE void
    QUEX_NAME(Mode_on_entry_exit_null_function)(QUEX_TYPE_ANALYZER* me, 
                                                const QUEX_NAME(Mode)* TheMode) 
    { }

#endif /* __QUEX_INCLUDE_GUARD__ANALYZER__MODE_I */
