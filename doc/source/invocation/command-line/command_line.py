#Command Line Options
#====================
import os
import sys
import re
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.input.setup import SETUP_INFO, SetupParTypes
from   quex.input.command_line.documentation import content 

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
            elif Default == SetupParTypes.INT_LIST:
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

print VisitorSphinx().do(content)
