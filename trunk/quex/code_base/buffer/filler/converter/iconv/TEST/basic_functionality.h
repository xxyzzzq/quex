#include <quex/code_base/test_environment/TestAnalyzer-configuration>
#include <quex/code_base/buffer/filler/converter/Converter>
#include <stdint.h>

QUEX_NAMESPACE_QUEX_OPEN

extern void test_conversion_in_one_beat(QUEX_NAME(Converter)* converter, 
                                        const char*           CodecName);

extern void test_conversion_stepwise_source(QUEX_NAME(Converter)* converter, 
                                            const char*           CodecName);

extern void test_conversion_stepwise_drain(QUEX_NAME(Converter)* converter, 
                                           const char*           CodecName);

QUEX_NAMESPACE_QUEX_CLOSE
