#! /usr/bin/env python
import sys
import os
sys.path.append("../../../../")
import generator_test

choice = generator_test.hwut_input("Simple: Maximum Length Match", "SAME;")

pattern_dict = { "DIGIT": "[0-9]" }
pattern_action_pair_list = [
    # keyword (need to come before identifier, because otherwise they would be overruled by it.)
    ('"if"',                     "IF"), 
    ('"else"',                   "ELSE"),
    ('"struct"',                 "STRUCT"),
    ('"for"',                    "FOR"),
    ('"typedef"',                "TYPEDEF"),
    ('"typedefun"',              "TYPEDEFUN"),
    ('"type"',                   "TYPE"),
    ('"def"',                    "DEF"),
    ('"fun"',                    "FUN"),
    ('"while"',                  "WHILE"),
    ('"return"',                 "RETURN"),
    # identifier
    ('[_a-zA-Z][_a-zA-Z0-9]*',   "IDENTIFIER"),
    # 
    ('"{"',                      "BRACKET_OPEN"),
    ('"}"',                      "BRACKET_CLOSE"),
    ('"("',                      "BRACKET_OPEN"),
    ('")"',                      "BRACKET_CLOSE"),
    ('";"',                      "SEMICOLON"),
    ('"="',                      "OP_ASSIGN"),
    ('"=="',                     "OP_COMPARISON"),
    ('"<"',                      "OP_CMP_LESS"),
    ('">"',                      "OP_CMP_GREATER"),
    ('"+"',                      "OP_PLUS"),
    ('"*"',                      "OP_MULT"),
    ('"++"',                     "OP_PLUS_PLUS"),
    ('{DIGIT}+("."{DIGIT}*)?',   "NUMBER"),
    ('[ \\t\\n]+',               "WHITESPACE")
]

test_str = """
struct MyType<T> {
   if( T == int ) typedef my_vars_type = string
   else           typedef my_vars_type = utf32_string
   typedefun      T
   my_vars_type   name
   my_vars_type   description
   def sin_cos(x) = sin(x) * cos(x)

   main()
      for(x = 0.12; x < 12 ; x++)
         print x * sin_cos(x)
      while( no_user_abort() ) sleep()

   fun   
"""

generator_test.do(pattern_action_pair_list, test_str, pattern_dict, choice, QuexBufferSize=64)
    
