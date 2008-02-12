#ifndef __INCLUDE_GUARD__QUEX_INCLUDE_COMPATIBILITY_INTTYPES_H__
#define __INCLUDE_GUARD__QUEX_INCLUDE_COMPATIBILITY_INTTYPES_H__
// NOTE: At the time of this writing (Aug. 2007) there are still some
//       compilers that do not support C99 Standard completely and
//       do not provided 'inttypes.h' and 'stdint.h' along with their
//       compiler package (e.g. a major Redmondian Company). For this
//       reason this header creates som adaptions.

extern "C" {
#ifdef _MSC_VER
#   include <quex/code_base/compatibility/win/inttypes.h>
#else
#   include <inttypes.h>
#endif
}

#endif // __INCLUDE_GUARD__QUEX_INCLUDE_COMPATIBILITY_INTTYPES_H__
