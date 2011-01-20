#! /usr/bin/env python
import sys
import os
from StringIO import StringIO
sys.path.append(os.environ["QUEX_PATH"])
import quex.output.cpp.token_class_maker         as token_class
import quex.input.token_type                     as parser
import quex.core_engine.generator.languages.core as languages
import quex.input.setup         

quex.input.setup.setup.buffer_element_size = 1
quex.input.setup.setup.output_token_class_file = ""
quex.input.setup.setup.token_class_name_space = ""
quex.input.setup.setup.token_class_name_safe = ""
quex.input.setup.setup.language_db = languages.db["C++"]

if "--hwut-info" in sys.argv:
    print "Token Class Template"
    sys.exit(0)

def test(Txt):
    sh = StringIO(Txt)
    sh.name = "a string"
    descriptor = parser.parse(sh)
    txt, txt_i = token_class._do(descriptor)
    print txt

test0 = "{ "
test1 = \
"""
{
   name = europa::deutschland::baden_wuertemberg::ispringen::MeinToken;
   distinct {
       my_name  :  std::string;
       numbers  :  std::vector<int>;
   }
   union {
       { 
          number       : float;
          index        : short;
       }
       { 
          x            : int16_t;
          y            : int16_t;
       }
       stream_position : uint32_t;
       who_is_that     : uint16_t;
   }
   constructor {
       this = is = a = constructor;
   }
   inheritable;
   destructor {
       this = is = a = destructor;
   }
   take_text {
       return true;
   }
   copy {
       this = is = a = copy-code;
   }
}
"""
test(test1)

