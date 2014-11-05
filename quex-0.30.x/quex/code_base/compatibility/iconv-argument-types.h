#ifndef __INCLUDE_GUARD__QUEX_INCLUDE_COMPATIBILITY_ICONV_ARGUMENT_TYPES_H__
#define __INCLUDE_GUARD__QUEX_INCLUDE_COMPATIBILITY_ICONV_ARGUMENT_TYPES_H__
// NOTE: At the time of this writing 'iconv' is delivered on different 
//       systems with different definitions for the second argument. The 
//       following 'hack' by Howard Jeng does the adaption automatically.
//
struct __Adapter_FuncIconv_SecondArgument {
    __Adapter_FuncIconv_SecondArgument(uint8_t ** in) : data(in) {}
    uint8_t ** data;
    operator const char **(void) const { return (const char **)(data); }
    operator       char **(void) const { return (      char **)(data); }
}; 

#endif // __INCLUDE_GUARD__QUEX_INCLUDE_COMPATIBILITY_ICONV_ARGUMENT_TYPES_H__
