#! /usr/bin/env python
import os
import sys
sys.path.append(os.environ["QUEX_PATH"])
import quex.output.cpp.codec_converter_helper as codec_converter_helper
import quex.engine.generator.languages.core as languages
import quex.engine.codec_db.core       as codec_db
import quex.input.setup

if "--hwut-info" in sys.argv:
    print "Converter: Determine UTF-8 Range Map for Codec"
    print "CHOICES:   cp737, cp866, cp1256;"
    sys.exit()

def test(CodecName):
    trafo_info          = codec_db.get_codec_transformation_info(CodecName)
    code_str, code0_str = codec_converter_helper._do(trafo_info, CodecName)
    fh = open("converter-tester.h", "w")
    fh.write(code_str + "\n" + code0_str)
    fh.close()
    define_str = "-DQUEX_TYPE_CHARACTER='unsigned char' " + \
                 "-DQUEX_INLINE=inline " + \
                 ("-D__QUEX_CODEC=%s " % CodecName) + \
                 "-D__QUEX_OPTION_LITTLE_ENDIAN " 

    compile_str = "g++ -ggdb -I./ -I$QUEX_PATH %s converter-tester.cpp -o converter-tester" % define_str
    print "##", compile_str
    os.system(compile_str)

    os.system("./converter-tester")
    #os.remove("./converter-tester.h")
    os.remove("./converter-tester")

quex.input.setup.setup.language_db = languages.db["C"]

test(sys.argv[1])

