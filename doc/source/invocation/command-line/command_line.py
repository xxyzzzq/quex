#Command Line Options
#====================
import os
import sys
import re
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.input.setup import SETUP_INFO, SetupParTypes

class SectionHeader:
    def __init__(self, Title): self.title = Title
    def do(self, visitor):     return visitor.do_SectionHeader(self.title)

class Text:
    def __init__(self, Text): self.text = Text
    def do(self, visitor):    return visitor.do_Text(self.text)

class Note:
    def __init__(self, *Content): self.content_list = list(Content)
    def do(self, visitor):        return visitor.do_Note(self.content_list)

class Block:
    def __init__(self, Content, Language="plain"):
        self.content  = Content
        self.language = Language
    def do(self, visitor): return visitor.do_Block(self.content, self.language)

class Option:
    def __init__(self, Name, CallStr, *Paragraphs):
        self.name           = Name
        self.call_str       = CallStr
        self.paragraph_list = list(Paragraphs)
    def do(self, visitor):
        info = SETUP_INFO[self.name]
        option_list = info[0]
        default     = info[1]
        return visitor.do_Option(option_list, self.call_str, default, self.paragraph_list)

class Item:
    def __init__(self, Name, *Paragraphs):
        self.name           = Name
        self.paragraph_list = list(Paragraphs)
    def do(self, visitor):
        return visitor.do_Item(self.name, self.paragraph_list)

class DescribeList:
    def __init__(self, Epilog, *Items):
        self.epilog    = Epilog
        self.item_list = list(Items)
    def do(self, visitor):
        return visitor.do_DescribeList(self.epilog, self.item_list)

class Visitor:
    re_verbatim = re.compile(r"\\v{([a-zA-Z0-9_ ]+)}")
    def __init__(self):
        self.nesting_level = -1

    def do(self, DescriptionList):
        def adapt(X):
            if isinstance(X, (str, unicode)): return Text(X)
            else:                             return X
        self.nesting_level += 1
        print "#DescriptionList:", DescriptionList
        adapted = [ adapt(x) for x in DescriptionList ]
        result  = [ x.do(self) for x in adapted ]
        for i, x in enumerate(result):
            print "#result %i: %s" % (i, x)
        self.nesting_level -= 1
        return "".join(result)

    def do_SectionHeader(self, Title): assert False
    def do_Note(self, ContentList):          assert False
    def do_Text(self, Text):          assert False
    def do_Block(self, Content, Language):      assert False
    def do_Option(self, OptionList, CallStr, Default, ParagraphList):        assert False
    def do_Item(self, Name, ParagraphList):          assert False
    def do_DescribeList(self, Epilog, ItemtList):  assert False

    def format_default(self, Default):
        if Default in SetupParTypes:
            if   Default == SetupParTypes.FLAG: 
                return "true (active)"
            elif Default == SetupParTypes.NEGATED_FLAG:
                return "false (inactive)"
            elif Default == SetupParTypes.LIST:
                return "empty list"
            else:
                assert False
        return "%s" % Default

    def format_block(self, Text):
        def get_indentation(Line):
            i = 0
            for i, letter in enumerate(Line):
                if not letter.isspace(): break
            return i
                
        min_indentation = 1e37
        line_list       = []
        for line in Text.split("\n"):
            line = line.replace("\t", "    ")
            # measure indentation
            indentation = get_indentation(line)
            if indentation < min_indentation: min_indentation = indentation
            line_list.append((indentation, line.strip()))

        # Indent everything starting with an indentation of 'Indentation'
        curr_indentation = 4 * self.nesting_level
        return "".join(
            " " * (indentation - min_indentation + curr_indentation) + line
            for indentation, line in line_list
        )

    def format_text(self, Text):
        """Separates paragraphs and reformats them so that they are
        properly indented.
        """
        def append(pl, p):
            if p is not None: 
                pl.append("".join(p))
        def clean(line):
            """Delete any prepending or trailing whitespace, let the only
            whitespace be ' '. Let all whitespace between words be ' '.
            """
            result = line.strip()
            result = result.replace("\n", " ")
            result = result.replace("\t", " ")
            while result.find("  ") != -1:
                result = result.replace("  ", " ")
            return result
        def add_line(p, line):
            cl = self.__format_text(clean(line))
            if p is None: p = [ cl ]
            else:         p.append("%s " % cl)
            return p

        paragraph_list = []
        paragraph      = None
        for line in Text.split("\n"):
            line = line.strip()
            if len(line) == 0: 
                append(paragraph_list, paragraph)
                paragraph = None
            else:              
                paragraph = add_line(paragraph, line)
        append(paragraph_list, paragraph)
        return paragraph_list
                
    def __format_text(self, X):
        """Replace text formatting markers by the language dependent
        markers. For that the following replacement strings must be
        defined.

        .re_verbatim_replace --> print in 're_verbatim_replace' for variable and function 
                      names.
        """
        result = X
        result = Visitor.re_verbatim.sub(self.re_verbatim_replace, result)
        return result

class VisitorSphinx(Visitor):
    """Produces code for 'sphinx documentation system'
    """
    re_verbatim_replace = r"``\1``"
    def __init__(self):
        Visitor.__init__(self)
    def do_SectionHeader(self, Title):
        return "%s\n%s" % (Title, "=" * len(Title))
    def do_Text(self, Text):          
        return "".join(self.format_text(Text))
    def do_Note(self, ContentList):
        return ".. note::\n%s\n" % self.do(ContentList)
    def do_Block(self, Content, Language):
        block = self.format_block(Content)
        return ".. code-block:: %s\n%s\n" % (Language, block)
    def do_Option(self, OptionList, CallStr, Default, ParagraphList):
        options_str = reduce(lambda a, b: "%s, %s" % (a, b), OptionList)
        content     = self.do(ParagraphList)
        default     = self.format_default(Default)
        return ".. cmdoption:: %s %s\n%s\n    Default: %s\n" \
               % (options_str, CallStr, content, default)
    def do_Item(self, Name, ParagraphList):
        content = self.do(ParagraphList)
        return ".. describe:: %s\n%s\n" % (Name, content)
    def do_DescribeList(self, Epilog, ItemtList):
        content = "".join(
            "* %s\n" % self.format_text(content)
            for content in ItemtList
        )
        return "%s\n%s\n" % (Epilog, content)

class VisitorManPage(Visitor):
    re_verbatim_replace = r"\n.I \1\n"

description = [
SectionHeader("Code Generation"),
"""
This section lists the command line options to control the behavior of the
generated lexical analyzer. Strings following these options must be either
without whitespaces or in quotes. Numbers are specified in C-like format 
as described in :ref:`sec-number-format`.
""",
Option("input_mode_files", "[file name]+",
    """
    The file names following ``-i`` are the files containing quex source
    code to be used as input.
    """),
Option("analyzer_class", "[name ::]+ name"
    """
    ``name`` = Name of the lexical analyser class that is to be created
    inside the namespace ``quex``. This name also determines the
    file stem of the output files generated by quex. At the same time, the
    name space of the analyzer class can be specified by means of a sequence
    separated by ``::``.
    """,
    """
    If no name space is specified, the analyzer is placed in name space
    ``quex`` for C++ and the root name space for C. If the analyzer shall be
    placed in the root name space shall be used a ``::`` must be proceeding
    the class name. The invocation
    """,
    Block("> quex ... -o MySpace::MySubSpace::MySubSubSpace::Lexer"),
    """
    specifies that the lexical analyzer class is ``Lexer`` and that it is located
    in the namespace ``MySubSubSpace`` which in turn is located ``MySubSpace`` which
    it located in ``MySpace``. A specification
    """,
    Block("> quex ... -o ::Lexer", "bash"),
    """sets up the lexical analyzer in the root namespace and
    """,
    Block("> quex ... -o Lexer", "bash"),
    """generates a lexical analyzer class ``Lexer`` in default namespace ``quex``.
    """
    ),
Option("output_directory", "directory",
    """
     ``directory`` = name of the output directory where generated files are 
     to be written. This does more than merely copying the sources to another
     place in the file system. It also changes the include file references
     inside the code to refer to the specified ``directory`` as a base.
    """),
Option("output_file_naming_scheme", "scheme",
    """
    Specifies the filestem and extensions of the output files. The provided
    argument identifies the naming scheme. 

    If the option is not provided, then the naming scheme depends on the 
    ``--language`` command line option. 
    """,
    DescribeList("C++", 
     "No extension for header files that contain only declarations.",
     " ``.i`` for header files containing inline function implementation.",
     " ``.cpp`` for source files."),
    DescribeList("C", 
     "``.h`` for header files.",
     "``.c`` for source files."),
    DescribeList("++",
     "``.h++`` for header files.",
     "``.c++`` for source files."),
    DescribeList("pp",
     "``.hpp`` for header files.",
     "``.cpp`` for source files."),
    DescribeList("cc",
     "``.hh`` for header files.",
     "``.cc`` for source files."),
    DescribeList("xx",
     "``.hxx`` for header files.",
     "``.cxx`` for source files."),
    """
    For ``C`` there is currently no different naming scheme supported.
    """),
Option("language", "name",
     DescribeList("Defines the programming language of the output. ``name`` can be",
     "``C`` for plain C code.",
     "``C++`` for C++ code.",
     "``dot`` for plotting information in graphviz format.")),

Option("character_display", "hex|utf8",
     DescribeList("""Specifies how the character of the state transition are to be displayed
     when `--language dot` is used.
     """,
     "``hex`` displays the Unicode code point in hexadecimal notation.",
     "``utf8`` is specified the character will be displayed 'as is' in UTF8 notation."),
      ),
Option("normalize_f", None,
    """
    If this option is set, the output of '--language dot' will be a normalized
    state machine. That is, the state numbers will start from zero. If this flag 
    is not set, the state indices are the same as in the generated code.
    """),
Option("buffer_based_analyzis_f", None,
    """
    Generates an analyzer that does not read from an input stream, but runs instead
    only on a buffer. 
    """),
Option("user_application_version_id", "string",
    """
    ``string`` = arbitrary name of the version that was generated. This string
    is reported by the `version()` member function of the lexical analyser. 
    """),
Option("mode_transition_check_f", None,
    """
    Turns off the mode transition check and makes the engine a little faster.
    During development this option should not be used. But the final lexical
    analyzer should be created with this option set. 
    """),
Option("single_mode_analyzer_f",  None,
    """
    In case that there is only one mode, this flag can be used to inform quex
    that it is not intended to refer to the mode at all. In that case no
    instance of the mode is going to be implemented. This reduces memory 
    consumption a little and may possibly increase performance slightly.
    """),
Option("string_accumulator_f",  None,
     """
     Turns the string accumulator option off. This disables the use of the string 
     accumulator to accumulate lexemes. See ':ref:`Accumulator`'.
     """),
Option("include_stack_support_f", None,
     """
     Disables the support of include stacks where the state of the lexical 
     analyzer can be saved and restored before diving into included files.
     Setting this flag may speed up a bit compile time
     """),
Option("post_categorizer_f", None, 
     """
     Turns the post categorizer option on. This allows a 'secondary'
     mapping from lexemes to token ids based on their name. See 
     ':ref:`PostCategorizer`'.
     """),
Option("count_line_number_f", None,
     """
     Lets quex generate an analyzer without internal line counting.
     """),
Option("count_column_number_f", None,
     """
     Lets quex generate an analyzer without internal column counting.
     """),
"""
If an independent source package is required that can be compiled without an 
installation of quex, the following option may be used
""",
Option("source_package_directory",  None,
     """
     Creates all source code that is required to compile the produced
     lexical analyzer. Only those packages are included which are actually
     required. Thus, when creating a source package the same command line
     'as usual' must be used with the added `--source-package` option.

     The string that follows is the directory where the source package is
     to be located.
     """),
"""
For the support of derivation from the generated lexical analyzer class the
following command line options can be used.
""",
Option("analyzer_derived_class_name", "name",
    """
    ``name`` = If specified, the name of the derived class that the user intends to provide
    (see section <<sec-formal-derivation>>). Note, specifying this option
    signalizes that the user wants to derive from the generated class. If this
    is not desired, this option, and the following, have to be left out. The 
    namespace of the derived analyzer class is specified analgously to the
    specification for `--analyzer-class`, as mentioned above.
    """),
Option("analyzer_derived_class_file", "file name",
    """
    ``file-name`` = If specified, the name of the file where the derived class is
    defined.  This option only makes sense in the context of optioin
    ``--derived-class``. 
    """),
Option("token_id_prefix", "prefix",
     """
     ``prefix`` = Name prefix to prepend to the name
     given in the token-id files. For example, if a token section contains
     the name ``COMPLEX`` and the token-prefix is ``TOKEN_PRE_``
     then the token-id inside the code will be ``TOKEN_PRE_COMPLEX``. 

     The token prefix can contain name space delimiters, i.e. ``::``. In
     the brief token senders the name space specifier can be left out.
     """),
Option("token_policy", "single|queue",
     """
     Determines the policy for passing tokens from the analyzer to the user. 
     It can be either 'single' or 'queue'.
     """), 

Option("token_memory_management_by_user_f", None,
     """
     Enables the token memory management by the user. This command line
     option is equivalent to the compile option
     """,
     Block("QUEX_OPTION_USER_MANAGED_TOKEN_MEMORY"),
     """
     It provides the functions ``token_queue_memory_switch(...)`` for
     token policy 'queue' and ``token_p_switch(...)`` for token policy
     'single'.
     """),
Option("token_queue_size", "number", 
     """
     In conjunction with token passing policy 'queue', ``number`` specifies
     the number of tokens in the token queue. This determines the maximum
     number of tokens that can be send without returning from the analyzer
     function.
     """), 

Option("token_queue_safety_border", "number", 
     """
     Specifies the number of tokens that can be sent at maximum as reaction to
     one single pattern match. More precisely, it determines the number of 
     token slots that are left empty when the token queue is detected to be
     full.
     """),

Option("token_id_counter_offset", "number",
     """
     ``number`` = Number where the numeric values for the token ids start
     to count. Note, that this does not include the standard token ids
     for termination, unitialized, and indentation error.
     """),
"""
Certain token ids are standard, in a sense that they are required for a
functioning lexical analyzer. Namely they are ``TERMINATION`` and
``UNINITIALIZED`` The default values of those do not follow the token id
offset, but are 0, 1, and 2. If they need to be different, they must be defined
in the ``token { ... }`` section, e.g.""",
Block("""
    token {
        TERMINATION   = 10001;
        UNINITIALIZED = 10002;
        ...
    }
"""),
"""
A file with token ids can be provided by the option
""",
Option("token_id_foreign_definition_file", "file name [[begin-str] end-str]",
       """
       ``file-name`` = Name of the file that contains an alternative definition
       of the numerical values for the token-ids.
        
       Note, that quex does not reflect on actual program code. It extracts the
       token ids by heuristics. The optional second and third arguments allow
       to restrict the region in the file to search for token ids. For example
       """,
       Block("""
           > quex ... --foreign-token-id-file my_token_ids.hpp yytokentype   '};' \
                      --token-prefix          Example::BisonicParser::token::
       """, "bash"),
       """
       reads only the token ids from the enum in the code fragment ``yytokentype``.
       """),
Option("token_id_foreign_definition_file_show_f", None,
     """
     If this option is specified, then Quex prints out the token ids which have
     been found in a foreign token id file.
     """),
"""
The following options support the definition of a independently customized token class:
""",
Option("token_class_file", "file name",
     """
     ``file name`` = Name of file that contains the definition of the
     token class. Note, that the setting provided here is possibly 
     overwritten if the ``token_type`` section defines a file name
     explicitly.
     """),
Option("token_class", "[name ::]+ name"
     """
     ``name`` is the name of the token class. Using '::'-separators it is possible
     to defined the exact name space as mentioned for the `--analyzer-class` command
     line option.
     """),
Option("token_id_type", "type name",
     """
     ``type-name`` defines the type of the token id. This defines internally the 
     macro ``QUEX_TYPE_TOKEN_ID``. This macro is to be used when a customized
     token class is defined. The types of Standard C99 'stdint.h' are encouraged.
     """),
Option("token_class_only_f", None,
     """
     When specified, quex only creates a token class. This token class differs
     from the normally generated token classes in that it may be shared between
     multiple lexical analyzers (see :ref:`sec-shared-token-class`).
     """,
     Note("""
     When this option is specified, then the LexemeNull is implemented along 
     with the token class. In this case all analyzers that use the token class, 
     shall define ``--lexeme-null-object`` according the token name space.
     """),
),
Option("external_lexeme_null_object", "variable", 
     """
     The 'name' is the name of the ``LexemeNull`` object. If the option is
     not specified, then this object is created along with the analyzer
     automatically. When using a shared token class, then this object must
     have been created along with the token class. Announcing the name of
     the lexeme null object princidences quex from generating a lexeme null
     inside the engine itself.
     """),
"""
There may be cases where the characters used to indicate buffer limit needs to
be redefined, because the default value appear in a pattern footnote:[As for
'normal' ASCII or Unicode based lexical analyzers, this would most probably not
be a good design decision. But, when other, alien, non-unicode codings are to
be used, this case is conceivable.].  The following option allows modification
of the buffer limit code:
""",
Option("buffer_limit_code", "number", 
     """Numberic value used to mark buffer borders. This should be a number that
     does not occur as an input character."""),
"""
On several occasions quex produces code related to 'newline'. The coding of 
newline has two traditions: The Unix tradition which codes it plainly as 0x0A, 
and the DOS tradition which codes it as 0x0D followed by 0x0A. To be on the 
safe side by default, quex codes newline as an alternative of both. In case,
that the DOS tradition is not relevant, some performance improvements might
be achieved, if the '0x0D, 0x0A' is disabled. This can be done by the 
following flag.
""",
Option("dos_carriage_return_newline_f", None, 
     """If specified, the DOS newline (0x0D, 0x0A) is not considered whenever
     newline is required."""),
"""
For unicode support it is essential to allow character conversion. Currently
quex can interact with GNU IConv and IBM's ICU library. For this 
the correspondent library must be installed on your system. On Unix systems, the iconv library
is usually present. Relying on IConv or ICU lets is a flexible solution. The generated
analyzer runs on converted content. The converter can be adapted dynamically. 
""",
Option("converter_iconv_f", None, 
     """
     Enable the use of the iconv library for character stream decoding.
     This is equivalent to defining '-DQUEX_OPTION_CONVERTER_ICONV'
     as a compiler flag. Depending on your compiler setup, you might have
     to set the '-liconv' flag explicitly in order to link against the IConv
     library.
     """),
Option("converter_icu_f", None,
     """
     Enable the use of IBM's ICU library for character stream decoding.
     This is equivalent to defining '-DQUEX_OPTION_CONVERTER_ICU'
     as a compiler flag. There are a couple of libraries that are required
     for ICU. You can query those using the ICU tool 'icu-config'. A command 
     line call to this tool with '--ldflags' delivers all libraries that need
     to be linked. A typical list is '-lpthread -lm -L/usr/lib -licui18n -licuuc 
     -licudata'."""),
"""
Alternatively, the engine can run directly on a specific coded, i.e. without a conversion
to Unicode. This approach is less flexible, but may be faster.
""",
Option("buffer_codec", "codec name",
     """
     Specifies a codec for the generated engine. By default the internal
     engine runs on Unicode code points. That is, the analyzer engine is
     transformed according to the given codec before code is generated.
     """,
     Note("""
     When ``--codec`` is specified the command line flag ``-b`` or
     ``--buffer-element-size`` does not represent the number of bytes
     per character, but *the number of bytes per code element*. The
     codec UTF8, for example, is of dynamic length and its code elements
     are bytes, thus only ``-b 1`` makes sense. UTF16 triggers on elements
     of two bytes, while the length of an encoding for a character varries.
     For UTF16, only ``-b 2`` makes sense.
     """),
),
Option("buffer_codec_file", "file name", 
     """
     By means of this option a freely customized codec can be defined. The
     ``file name`` determines at the same time the file where
     the codec mapping is described and the codec's name. The codec's name
     is the directory-stripped and extension-less part of the given
     follower.  Each line of such a file must consist of three numbers, that
     specify 'source interval begin', 'source interval length', and 'target
     interval end. Such a line specifies how a cohesive Unicode character
     range is mapped to the number range of the customized codec. For
     example, the mapping for codec iso8859-6 looks like the following.
     """,
     Block("""
                    0x000 0xA1 0x00
                    0x0A4 0x1  0xA4
                    0x0AD 0x1  0xAD
                    0x60C 0x1  0xAC
                    0x61B 0x1  0xBB
                    0x61F 0x1  0xBF
                    0x621 0x1A 0xC1
                    0x640 0x13 0xE0
     """),
     """
     Here, the Unicode range from 0 to 0xA1 is mapped one to one from Unicode to 
     the codec. 0xA4 and 0xAD are also the same as in Unicode. The remaining
     lines describe how Unicode characters from the 0x600-er page are mapped 
     inside the range somewhere from 0xAC to 0xFF.
     """,
     Note("""
     This option is only to be used, if quex does not support the codec
     directly. The options ``--codec-info`` and ``--codec-for-language`` help to
     find out whether Quex directly supports a specific codec. If a ``--codec-file``
     is required, it is advisable to use ``--codec-file-info  file-name.dat`` to
     see if the mapping is in fact as desired.""")),
"""The buffer on which a generated analyzer runs is characterized by its size 
(macro QUEX_SETTING_BUFFER_SIZE), by its element's size, and their type. The latter
two can be specified on the command line.

In general, a buffer element contains what causes a state transition 
in the analyzer. In ASCII code, a state transition happens on one byte 
which contains a character. If converters are used, the internal buffer
runs on plain Unicode. Here also, a character occupies a fixed number
of bytes. The check mark in 4 byte Unicode is coded as as 0x00001327.
It is treated as one chunk and causes a single state transition.

If the internal engine runs on a specific codec (``--codec``) which is
dynamic, e.g. UTF8, then state transitions happen on parts of a character.
The check mark sign is coded in three bytes 0xE2, 0x9C, and 0x93. Each
byte is read separately and causes a separate state transition.
""",
Option("buffer_element_size", "1|2|4",
     """
     With this option the number of bytes is specified that a buffer 
     element occupies. 
        
     The size of a buffer element should be large enough so that it can
     carry the Unicode value of any character of the desired input coding
     space.  When using Unicode, to be safe '-b 4' should be used except that
     it is unconceivable that any code point beyond 0xFFFF ever appears. In
     this case '-b 2' is enough.

     When using dynamic sized codecs, this option is better not used. The
     codecs define their chunks themselves. For example, UTF8 is built upon
     one byte chunks and UTF16 is built upon chunks of two bytes. 
     """,
     Note("""
        If a character size different from one byte is used, the 
        ``.get_text()`` member of the token class does contain an array
        that particular type. This means, that ``.text().c_str()``
        does not result in a nicely printable UTF8 string. Use
        the member ``.utf8_text()`` instead."""),
      ),
Option("buffer_element_type", "type name",
     """
     A flexible approach to specify the buffer element size and type is by
     specifying the name of the buffer element's type, which is the purpose
     of this option. Note, that there are some 'well-known' types such as
     ``uint*_t`` (C99 Standard), ``u*`` (Linux Kernel), ``unsigned*`` (OSAL)
     where the ``*`` stands for 8, 16, or 32. Quex can derive its size 
     automatically.

     Quex tries to determine the size of the buffer element type. This size is
     important to determine the target codec when converters are used. That
     is, if the size is 4 byte a different Unicode codec is used then if it
     was 2 byte. If quex fails to determine the size of a buffer element from
     the given name of the buffer element type, then the Unicode codec must
     be specified explicitly by '--converter-ucs-coding-name'.

     By default, the buffer element type is determined by the buffer element 
     size.
     """),

Option("buffer_byte_order", "little|big|<system>",
       """
        There are two types of byte ordering for integer number for different CPUs.
        For creating a lexical analyzer engine on the same CPU type as quex runs
        then this option is not required, since quex finds this out by its own.
        If you create an engine for a different plattform, you must know its byte ordering
        scheme, i.e. little endian or big endian, and specify it after ``--endian``. 
        """,
        DescribeList("""
        According to the setting of this option one of the three macros is defined 
        in the header files:
        """,
        "``__QUEX_OPTION_SYSTEM_ENDIAN``",
        "``__QUEX_OPTION_LITTLE_ENDIAN`",
        "``__QUEX_OPTION_BIG_ENDIAN`",
        ),
        """
        Those macros are of primary use for character code converters. The
        converters need to know what the analyser engines number representation
        is. However, the user might want to use them for his own special
        purposes (using ``#ifdef __QUEX_OPTION_BIG_ENDIAN ... #endif``).
        """),
"""
The implementation of customized converters is supported by the following options.
""",
Option("converter_user_new_func", "function name",
     """
     With the command line option above the user may specify his own
     converter. The string that follows the option is the name of the
     converter's ``_New`` function. When this option is set, automatically
     customized user conversion is turned on.
     """),
Option("converter_ucs_coding_name", "name", 
     """
     Determines what string is passed to the converter so that it converters
     a codec into unicode. In general, this is not necessary. But, if a 
     unknown user defined type is specified via '--buffer-element-type' then
     this option must be specified.

     By default it is defined based on the buffer element type.
     """),
"""
Template and Path Compression can be controlled with the following command line options:
""",
Option("compression_template_f", None, 
     """
     If this option is set, then template compression is activated.
     """),
Option("compression_template_min_gain", "number", 
     """
     The number following this option specifies the template compression coefficient.
     It indicates the relative cost of routing to a target state compared to a simple
     'goto' statement. The optimal value may vary from processor platform to processor
     platform, and from compiler to compiler.
     """), 
Option("compression_path_f", None, 
     """
     This flag activates path compression. By default, it compresses any sequence
     of states that allow to be lined up as a 'path'. This includes states of 
     different acceptance values, store input positions, etc.
     """),
Option("compression_path_uniform_f", None, 
     """
     This flag enables path compression. In contrast to the previous flag it 
     compresses such states into a path which are uniform. This simplifies
     the structure of the correspondent pathwalkers. In some cases this might
     result in smaller code size and faster execution speed.
     """),
Option("path_limit_code", "number",
     """
     Path compression requires a 'pathwalker' to determine quickly the end of 
     a path. For this, each path internally ends with a signal character, the
     'path termination code'. It must be different from the buffer limit code
     in order to avoid ambiguities. 
       
     Modification of the 'path termination code' makes only sense if the input
     stream to be analyzed contains the default value.
     """),
"""
The following options control the comment which is added to the generated code:
""",
Option("comment_state_machine_f", None, 
     """
     With this option set a comment is generated that shows all state transitions
     of the analyzer in a comment at the begin of the analyzer function. The format
     follows the scheme presented in the following example
     """,
     Block("""
            /* BEGIN: STATE MACHINE
             ...
             * 02353(A, S) <~ (117, 398, A, S)
             *       <no epsilon>
             * 02369(A, S) <~ (394, 1354, A, S), (384, 1329)
             *       == '=' ==> 02400
             *       <no epsilon>
             ...
             * END: STATE MACHINE
             */
     """, "cpp"),
     """
     It means that state 2369 is an acceptance state (flag 'A') and it should store
     the input position ('S'), if no backtrack elimination is applied. It originates
     from pattern '394' which is also an acceptance state and '384'. It transits to
     state 2400 on the incidence of a '=' character.
     """),
Option("comment_transitions_f", None, 
     """
     Adds to each transition in a transition map information about the characters 
     which trigger the transition, e.g. in a transition segment implemented in a 
     C-switch case construct
     """,
     Block("""
           ...
           case 0x67: 
           case 0x68: goto _2292;/* ['g', 'h'] */
           case 0x69: goto _2295;/* 'i' */
           case 0x6A: 
           case 0x6B: goto _2292;/* ['j', 'k'] */
           case 0x6C: goto _2302;/* 'l' */
           case 0x6D:
           ...
     """),
     """
     The output of the characters happens in UTF8 format.
     """),
Option("comment_mode_patterns_f", None, 
     """
     If this option is set a comment is printed that shows what pattern is present 
     in a mode and from what mode it is inherited. The comment follows the following
     scheme:
     """,
     Block("""
           /* BEGIN: MODE PATTERNS 
            ...
            * MODE: PROGRAM
            * 
            *     PATTERN-ACTION PAIRS:
            *       (117) ALL:     [ \r\n\t]
            *       (119) CALC_OP: "+"|"-"|"*"|"/"
            *       (121) PROGRAM: "//"
            ...
            * END: MODE PATTERNS
            */
     """, "cpp"),
     """
     This means, that there is a mode ``PROGRAM``. The first three pattern are related
     to the terminal states '117', '119', and '121'. The whitespace pattern of 117 was
     inherited from mode `ALL`. The math operator pattern was inherited from mode
     ``CALC_OP`` and the comment start pattern "//" was implemented in ``PROGRAM`` 
     itself.
     """),
"""
The comment output is framed by ``BEGIN:`` and ``END:`` markers. This facilitates the extraction
of this information for further processing. For example, the Unix command 'awk' can be used:
""",
Block("""
   awk 'BEGIN {w=0} /BEGIN:/ {w=1;} // {if(w) print;} /END:/ {w=0;}' MyLexer.c
""", "bash"),
"""When using multiple lexical analyzers it can be helpful to get precise 
information about all related name spaces. Such short reports on the standard
output are triggered by the following option.
""",
Option("show_name_spaces_f", None, 
     """
     If specified short information about the name space of the analyzer and the
     token are printed on the console. 
     """),
SectionHeader("Errors and Warnings"),
"""
When the analyzer behaves unexpectedly, it may make sense to ponder over low-priority
patterns outrunning high-priority patterns. The following flag supports these considerations.
""",
Option("warning_on_outrun_f", None, 
     """
     When specified, each mode is investigated whether there are patterns of lower
     priority that potentially outrun patterns of higher priority. This may happen
     due to longer length of the matching lower priority pattern. 
     """),
"""
Some warnings, notes, or error messages might not be interesting or even
be disturbing for the user. For such cases, quex provides an interface to 
avoid prints on the standard output.
""",
Option("suppressed_notification_list", "[integer]+", 
    """
    By this option, errors, warnings, and notes may be suppressed. The 
    option is followed by a list of integers--each integer represents
    a suppressed message.
    """),
"""
The following enumerates suppress codes together with their associated messages.
""",
Item("0", 
     """
     Warning if quex cannot find an included file while        
     diving into a 'foreign token id file'.                    
     """),
Item("1",
     """
    A token class file (``--token-class-file``) may           
    contain a section with extra command line arguments       
    which are reported in a note.                             
     """),
Item("2",
     """
    Error check on dominated patterns,                        
    i.e. patterns that may never match due to higher          
    precedence patterns which cover a superset of lexemes.    
     """),
Item("3",
     """
    Error check on special patterns (skipper, indentation,    
    etc.) whether they are the same.                          
     """),
Item("4",
     """
    Warning or error on 'outrun' of special patterns due to   
    lexeme length. Attention: To allow this opens the door to 
    very confusing situations. For example, a comment skipper 
    on "/*" may not trigger because a lower precedence pattern
    matches on "/**" which is longer and therefore wins.      
     """),
Item("5",
     """
    Detect whether higher precedence patterns match on a      
    subset of lexemes that a special pattern (skipper,        
    indentation, etc.) matches. Attention: Allowing such      
    behavior may cause confusing situations. If this is       
    allowed a pattern may win against a skipper, for example. 
    It is the expectation, though, that a skipper shall skip  
    --which it cannot if such scenarios are allowed.          
     """),
Item("6",
     """
    Warning if no token queue is used while some              
    functionality might not work properly.                    
     """),
Item("7",
     """
    Warning if token ids are used without being explicitly    
    defined.                                                  
     """),
Item("8",
     """
    Warning if a token id is mentioned as a 'repeated token'  
    but has not been defined.                                 
     """),
Item("9",
     """
    Warning if a prefix-less token name starts with the       
    token prefix.                                             
     """),
Item("10",
     """
    Warning if there is no 'on_codec_error' handler while a   
    codec different from unicode is used.                     
     """),
Item("11",
     """
    Warning a counter setup is defined without specifying a   
    newline behavior.                                         
     """),
Item("12",
     """
    Warning if a counter setup is defined without an          
    ``\else`` section.                                        
     """),
Item("13",
     """
    If there is a counter setup without newline defined, quex 
    tries to implement a default newline as hexadecimal 0A or 
    0D.0A.                                                    
     """),
Item("14",
     """
    Same as 13, except with hexadecimal '0D'.                 
     """),
Item("15",
     """
    Warning if a token type has no 'take_text' member         
    function. It means, that the token type has no interface  
    to automatically accept a lexeme or and accumulated       
    string.                                                   
     """),
Item("16",
     """
    Warning if there is a string accumulator while            
    '--suppress 15' has been used.                            
     """),
SectionHeader("Queries"),
"""
The former command line options influenced the procedure of code generation.
The options to solely query quex are listed in this section. First of all the two
traditional options for help and version information are
""",
Option("query_help_f", None,
       """Reports some help about the usage of quex on the console.
       """),
Option("query_version_f", None,
       """Prints information on the version of quex.
       """),
"""
The following options allow to query on character sets and the result
of regular expressions.
""",
Option("query_codec", "name",
       """
   Displays the characters that are covered by the given codec's name. If the
   name is omitted, a list of all supported codecs is printed. Engine internal
   character encoding is discussed in section :ref:`sec-engine-internal-coding`.
       """),
Option("query_codec_file", "file name", 
       """
   Displays the characters that are covered by the codec provided in the
   given file. This makes sense in conjunction with ``--codec-file`` where 
   customized codecs can be defined.
       """),
Option("query_codec_for_language", "language", 
       """
   Displays the codecs that quex supports for the given human language. If the
   language argument is omitted, all available languages are listed.
       """),
Option("query_property", "property", 
       """
   Displays information about the specified Unicode property.
   The ``property`` can also be a property alias. If ``property``
   is not specified, then brief information about all available Unicode
   properties is displayed.
       """),
Option("query_set_by_property", "setting", 
       """
   Displays the set of characters for the specified Unicode property setting. 
   For query on binary properties only the name is required. All other
   properties require a term of the form ``name=value``.
       """),
Option("query_property_match", "wildcard-expression", 
       """
       Displays property settings that match the given wildcard expression. This
       helps to find correct identifiers in the large list of Unicode settings.
       For example, the wildcard-expression ``Name=*LATIN*`` gives all settings
       of property ``Name`` that contain the string ``LATIN``.
       """),
Option("query_set_by_expression", "regular expression", 
       """
       Displays the resulting character set for the given regular expression.
   Character set expressions that are ususally specified in ``[: ... :]`` brackets
   can be specified as expression. To display state machines, it may be best
       to use the '--language dot' option mentioned in the previous section.
       """),
Option("query_numeric_f", None, 
       """
   If this option is specified the numeric character codes are displayed rather
   then the utf8 characters.
       """),
Option("query_intervals_f", None, 
       """
   This option disables the display of single character or single character codes.
   In this case sets of adjacent characters are displayed as intervals. This provides
   a somewhat more abbreviated display.
       """),
]

print VisitorSphinx().do(description)
