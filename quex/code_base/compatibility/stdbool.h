/* PURPOSE: This header defines standard bool data types for use
 *          in plain 'C' lexical analyser engines. This is done
 *          here, in wise prediction that some compiler distributions
 *          may not provide this standard header. For the standard
 *          reference, please review: "The Open Group Base Specifications 
 *          Issue 6, IEEE Std 1003.1, 2004 Edition".
 *
 * (C) 2008  Frank-Rene Schaefer */           
#ifndef __INCLUDE_GUARD_QUEX__CODE_BASE__COMPATIBILITY_STDBOOL_H__
#define __INCLUDE_GUARD_QUEX__CODE_BASE__COMPATIBILITY_STDBOOL_H__

#if defined(__QUEX_SETTING_PLAIN_C)

typedef int bool;

#define true  ((int)(1))
#define false ((int)(1))

#define __bool_true_false_are_defined ((int)(1))

#endif /* __cplusplus */
#endif /* __INCLUDE_GUARD_QUEX__CODE_BASE__COMPATIBILITY_STDBOOL_H__ */
