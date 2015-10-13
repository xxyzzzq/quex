#ifndef QUEX_INCLUDE_GUARD_BUFFER_BASIC_FUNCTIONALITY
#define QUEX_INCLUDE_GUARD_BUFFER_BASIC_FUNCTIONALITY

#include <quex/code_base/test_environment/TestAnalyzer-configuration>
#include <quex/code_base/definitions>
#include <quex/code_base/buffer/Buffer>
#include <quex/code_base/MemoryManager>
#include <hwut_unit.h>

QUEX_NAMESPACE_MAIN_OPEN

bool        basic_functionality(QUEX_NAME(Buffer)* me, const char* ReferenceFileName);
const char* find_reference(const char* file_stem);

QUEX_NAMESPACE_MAIN_CLOSE

#endif /* QUEX_INCLUDE_GUARD_BUFFER_BASIC_FUNCTIONALITY */
