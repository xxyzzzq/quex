from distutils.core import setup

setup(name         = 'quex',
      version      = '0.8.1',
      author       = 'Frank-Rene Schaefer',
      author_email = 'fschaef@users.sourceforge.net',
      url          = 'quex.sf.net',
      ##
      data_files   = ['./templates', ['./templates/*'],
                      './',          ['./LPGL.txt'],
                      './TEST',      ['./TEST/*']],
      py_modules   = [ "file_in.py",             "GetPot.py",
                       "quex_token_id_maker.py", "pre_flex.py",
                       "lexer_mode.py",          "quex.py",
                       "setup_parser.py",        "quex_class_out.py",
                       "error_msg.py",           "install-unix.sh",
                       "modes_in.py",            "modes_out.py",
                       "post_flex.py"],
      )

