from distutils.core import setup

# number of test applications for quex
TEST_N = 3

# template files for cpp code generation
cpp_template_files_pre = [ "circular_queue", "quex", "token",
                           "token.cpp", "token_queue" ]

cpp_template_files = map(lambda filename: "templates/" + filename,
                         cpp_template_files_pre)


# test files to be packed with quex
test_files_pre = ['in/token.dat', 'in/simple.qx', 'in/PATTERNS.lex',
              'Makefile', 'lexer.cpp', 'example.txt' ]

test_files = []
for i in range(3):
    test_files.extend(map(lambda filename: "TEST/%03i/%s" % (i, filename),
                          test_files_pre))


setup(name         = 'quex',
      version      = '0.8.1',
      author       = 'Frank-Rene Schaefer',
      author_email = 'fschaef@users.sourceforge.net',
      url          = 'quex.sf.net',
      ##
      package_dir  = { '': '/tmp/test0/quex'},
      data_files   = [ ('templates', cpp_template_files),
                       ('./',        ['LPGL.txt']),
                       ('TEST',      test_files)
                     ],
      ##
      py_modules   = [ "DEFINITIONS",
                       "file_in",             "GetPot",
                       "quex_token_id_maker", "pre_flex",
                       "lexer_mode",          "quex",
                       "setup_parser",        "quex_class_out",
                       "error_msg",           "modes_in",
                       "modes_out",           "post_flex"],
      )

