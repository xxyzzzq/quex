#! /usr/bin/env python
import os
import sys
sys.path.append(os.environ["QUEX_PATH"])
import quex.output.cpp.converter as converter
import quex.input.codec_db       as codec_db

if "--hwut-info" in sys.argv:
    print "Converter: Determine UTF-8 Range Map for Codec"
    print "CHOICES:   cp737, cp866, cp1256;"
    sys.exit()

def test(CodecName):
    trafo_info = codec_db.get_codec_transformation_info(CodecName)
    code_str   = converter.write(trafo_info, CodecName)
    fh = open("converter-tester.h", "w")
    fh.write(code_str)
    fh.close()
    define_str = "-DCONVERT_TO_UTF8=Quex_%s_to_utf8_string " % CodecName + \
                 "-DQUEX_TYPE_CHARACTER='unsigned char' " + \
                 "-DQUEX_INLINE=inline " + \
                 "-D__QUEX_CODEC=\\\"%s\\\" " % CodecName + \
                 "-D__QUEX_OPTION_LITTLE_ENDIAN"

    compile_str = "g++ -ggdb -I./ -I$QUEX_PATH %s converter-tester.cpp -o converter-tester" % define_str
    print "##", compile_str
    os.system(compile_str)

    os.system("./converter-tester")
    os.remove("./converter-tester.h")
    os.remove("./converter-tester")

test(sys.argv[1])

