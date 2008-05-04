// : -*- C++ -*-  vim: set syntax=cpp:
//
// (C) 2007 Frank-Rene Schaefer
//
#ifndef __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_CORE_I_
#define __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_CORE_I_

#include <quex/code_base/buffer/input_strategy>

#include <iostream>

#include <cassert>
extern "C" {
#include <quex/code_base/compatibility/inttypes.h>
}
#include<cstdlib>
#include<cstring>

namespace quex {

#   define TEMPLATE_IN template<class CharacterType> inline
#   define CLASS       buffer<CharacterType>   


#undef TEMPLATE_IN
#undef CLASS
}

#endif // __INCLUDE_GUARD_QUEX_BUFFER_BUFFER_CORE_I_
