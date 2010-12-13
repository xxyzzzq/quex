from quex.input.setup import setup as Setup
"""
find quex/code_base \
     -path "*.svn*"        -or -path "*TEST*" -or -name tags      \
     -or -name "TXT*"      -or -name "*.txt"  -or -name "*.sw?"   \
     -or -path "*DESIGN*"  -or -name "*.7z"   -or -name "*ignore" \
     -or -name "*DELETED*" -or -name .        -or -name "*_body"  \
     -or -name "[1-9]"     -or -name "°"      -or -name "*.o"     \
     -or -name "*.exe"     -prune  \
     -or -type f -print | sort
"""

analyzer_accumulator = """
/analyzer/Accumulator
/analyzer/Accumulator.i
"""

analyzer_counter = """
/analyzer/Counter
/analyzer/Counter.i
"""

analyzer_post_categorizer = """
/analyzer/PostCategorizer
/analyzer/PostCategorizer.i
"""

analyzer_include_state = """
/analyzer/member/include-stack
/analyzer/member/include-stack.i
"""

analyzer_base = """
/analyzer/C-adaptions.h
/analyzer/Mode
/analyzer/Mode.i
/analyzer/asserts
/analyzer/asserts.i
/analyzer/configuration/derived
/analyzer/configuration/undefine
/analyzer/configuration/validation
/analyzer/headers
/analyzer/headers.i
/analyzer/member/basic
/analyzer/member/basic.i
/analyzer/member/buffer-access
/analyzer/member/buffer-access.i
/analyzer/member/constructor
/analyzer/member/constructor.i
/analyzer/member/misc
/analyzer/member/misc.i
/analyzer/member/mode-handling
/analyzer/member/mode-handling.i
/analyzer/member/navigation
/analyzer/member/navigation.i
/analyzer/member/on_indentation.i
/analyzer/member/token-receiving
/analyzer/member/token-receiving.i
/analyzer/member/token-sending
/analyzer/member/token-sending-undef.i
"""

compatibility = """
/compatibility/iconv-argument-types.h
/compatibility/inttypes.h
/compatibility/pseudo-stdbool.h
/compatibility/stdbool.h
/compatibility/win/borland_inttypes.h
/compatibility/win/msc_inttypes.h
/compatibility/win/msc_stdint.h
"""

converter_helper = """
/converter_helper/base-char-and-wchar.gi
/converter_helper/base-core.g
/converter_helper/base-core.gi
/converter_helper/base.g
/converter_helper/base.gi
/converter_helper/base-unicode.gi
/converter_helper/unicode
/converter_helper/unicode.i
/converter_helper/utf16
/converter_helper/utf16.i
/converter_helper/utf32
/converter_helper/utf32.i
/converter_helper/utf8
/converter_helper/utf8.i
"""

token = """
/token/CDefault.qx
/token/CppDefault.qx
/token/TokenPolicy
/token/TokenQueue
/token/TokenQueue.i
"""

buffer = """
/buffer/asserts
/buffer/Buffer
/buffer/Buffer_debug.i
/buffer/Buffer.i
/buffer/MemoryPositionMimiker
"""

buffer_filler = """
/buffer/BufferFiller
/buffer/BufferFiller.i
/buffer/InputPolicy
"""

buffer_filler_plain = """
/buffer/plain/BufferFiller_Plain
/buffer/plain/BufferFiller_Plain.i
"""

buffer_filler_converter = """
/buffer/converter/BufferFiller_Converter
/buffer/converter/BufferFiller_Converter.i
/buffer/converter/Converter
"""

buffer_filler_iconv = """
/buffer/converter/iconv/Converter_IConv
/buffer/converter/iconv/Converter_IConv.i
/buffer/converter/iconv/special_headers.h
"""

buffer_filler_icu = """
/buffer/converter/icu/Converter_ICU
/buffer/converter/icu/Converter_ICU.i
/buffer/converter/icu/special_headers.h
"""

base = """
/asserts
/aux-string
/aux-string.i
/core.mkd
/definitions
/include-guard-undef
/MemoryManager
/MemoryManager.i
/temporary_macros_off
/temporary_macros_on
"""

def do():
    pass
