.. _sec:pattern-pitfalls:

Pattern Matching
-----------------

Predence has been defined in terms of *match length* and *pattern position*
(see :ref:`sec:match-precendence`). Length decides first. Then, if two pattern
match the same lexeme, the pattern that is defined *before* the other
pattern has precedence.  Thus, if there are for example two patterns

.. code-block:: cpp

     [a-z]+     => TKN_IDENTIFIER(Lexeme);
     "print"    => TKN_KEYWORD_PRINT;

then the keyword ``print`` will never be matched. This is so, because ``[a-z]``
matches also the character chain ``print`` and has a higher precedence, because
it is defined first. However, in such a situation an appropriate warning will
be issued. 

The 'greedy match' approach, i.e. that the pattern with the longest matching
lexeme wins inhabits a subtle danger, that cannot be caught by the lexical
analyzer generator. Imagine, a mode defines a pattern-action pair as below.

.. code-block:: cpp

      ...
      cup    => QUEX_TKN_KEYWORD_CUP;
      [a-z]+ => QUEX_TKN_IDENTIFIER(Lexeme);
      ...

When such a mode is fed with "cup holder", it is expected to produce the plain
token ``CUP`` and the token ``IDENTIFIER`` carrying "holder" as text. However,
let at some later position--may be in a derived mode--the following pattern-
action pair be defined.

.. code-block:: cpp

      ...
      "cup"[ \t\n]+"holder" => TKN_KEYWORD_CUP_HOLDER;
      ...

Then, the input "cup holder" would produce a single token ``CUP_HOLDER``,
because the according pattern matches a longer lexeme than ``cup`` alone.

  .. warning::

     Lower priority patterns may very well win against high-priority patterns
     if they match longer lexemes. Consequently, patterns in derived modes may
     win against patterns in base modes. As mentioned earlier [#f2]_ , the
     polymorphism-assumption, i.e. that derived modes behave like base modes on
     the same content cannot be made. 
     
In practical applications, an inadvert 'pattern competition' results in an
analyzer that seems to work sometimes and sometimes not. The functioning often
appears to be related to padding characters and white space. This state of
affairs cannot be simply turned off. It has its roots in the longest match
approach which is an essential characteristic of lexical analyzer generation
and has its rationale [f#3]_.  However, it is possible to detect cases of
outrunning patterns by the command line option '--warning-on-outrun' (or
shortly '--woo'). The aforementioned example of the 'cup holder', would
trigger a notification such as the following.::

    mine.qx:81:warning: The pattern '"cup"[ \t\n]+"holder"' has lower priority but
    mine.qx:11:warning: may outrun pattern 'cup' as defined here.

Greedy matching can be tricked, by the usage of anti-patterns (see section
:ref:`sec:anti-patterns`). For this, the IDENTIFIER should be expressed in
terms of anti-patterns, i.e.::

      key           => TKN_KEYWORD;
      \A{key}[a-z]+ => TKN_IDENTIFIER;

If more than one KEYWORD are involved, e.g. 'key', 'password', and 'secret', 
the IDENTIFIER would have to look like::

      \A{key|password|secret}[a-z]+ => TKN_IDENTIFIER;
    
Another pitfall is related to character codes that the lexical analyser uses to
indicate the *buffer-limit*. The values for those codes are chosen to be out of
the range for sound regular expressions parsing human written text (0x0 for
buffer-limit). If it is intended to parse binary files, and this value is
supposed to occur in patterns, then its code need to be changed.  Section
:ref:`sec:command-line` mentions how to specify the buffer limit
code on the command line.

Another unexpected behavior may occurr if characters appear as normal text
elements and at the same time as range delimiters. This resulted once in a
bug report which is shown in the following example. A pattern ``P_XML`` had
to match XML tags in arrow brackets and was defined as below. 

.. code-block:: cpp

   define {
       P_XML   <\/?[A-Za-z!][^>]*>
   }

It now happened, that the following text fragment inside an XML tag contained a
lesser sign.::

   La funzione di probabilità è data da ove "k" e "r" sono interi non
   negativi e "p" una probabilità (0<p<1) La funzione generatrice dei 
   momenti è: A confronto con le due ...

The occurence of ``<`` in "(0<p<1)" opens the ``P_XML`` pattern and lets the
analyzer search for the closing ``>``. Anything between the lesser sign and the
next greater sign would be interpreted as XML tag title--nonsense.  To cope
with this situations such text regions must be protected from a lurking
``P_XML`` pattern. It is appropriate to to parse such text content in a
separate mode. Alternatively, assuming that that XML files are well-formed
documents :cite:`Bray1998extensible`, the begin-of-line delimiter ``^`` might
restrict the match domain sufficiently, such that ``P_XML`` is defined as. 

.. code-block:: cpp

   define {
       P_XML   ^[ \t]*<\/?[A-Za-z!][^>]*>
   }

Another pitfall is related to this begin-of-line pre-condition ``^``: *It does
not always match the begin of a line!* It only matches the begin of a line if
the analysis step starts at the begin of a line. It may fail to do so if
another pattern includes newline among things that match the beginning of the
begin-of-line pattern. Consider the following.

.. code-block:: cpp

    mode EXAMPLE {
        [ \n]+     => QUEX_TKN_WHITESPACE;
        ^[ ]*hello => QUEX_TKN_GREETING(Lexeme);
    }

It might come as a supprise that the input "   \n hello" does not trigger the
sending of ``GREETING``. This is so since ``[ \n]`` matches "   \n ", i.e.
even the whitespace following the newline. The next analysis step starts at
"hello" which is not directly preceeded by ``\n``.  Splitting the white space
eater into newline and non-newline helps:

.. code-block:: cpp

    mode EXAMPLE {
        [ ]+        => TKN_WHITESPACE;
        [\n]+       => TKN_WHITESPACE;
        ^[ ]*hello  => TKN_GREETING(Lexeme);
    }

Now, the input "   \n hello" is matched appropriately. First, ``[ ]+`` matches
and leaves "\n hello". Second, ``[\n]+`` matches, and leaves " hello"--which is
directly preceeded by newline. Now, the begin-of-line pre-condition holds and
the pattern ``^[ ]*hello`` can match.

There is a crucial difference between the *matching lexeme* and the *core
lexeme* when it comes to post-contexts. Let a pattern with post-context be
defined as ``hello/"!"``, i.e. it matches "hello" when it is followed by "!".
The matching lexeme, then, is "hello!" but the core lexeme is "hello". The next
analysis step starts at "!". The pattern action 'sees' the core lexeme, but in
the precedence competition the length of the matching lexeme decides. This may
lead to confusion. Consider the the example below.

.. code-block:: cpp

    define {
        NUMBER   [0-9]+
        FUNCTION [a-z]+/"("{NUMBER}?")"
        PROPERTY [a-z]+"()"
    }
    mode EXAMPLE {
        {FUNCTION} => QUEX_TKN_FUNCTION(Lexeme);
        {PROPERTY} => QUEX_TKN_PROPERTY(Lexeme);
    }

It might be plausible to assume that the input "some()" will cause
``{PROPERTY}`` to match, because the matching lexeme is "some()".
``{FUNCTION}`` matches on "some()", but the core lexeme is "some" and "()" is
left for the next step.  However, as said, first the length of the matching
lexeme is taken into account. It is the same for both. Second, the pattern
position is considered. ``{FUNCTION}`` wins since it comes before
``{PROPERTY}``.


.. rubric:: Footnotes

.. [#f2] See section :ref:`sec:inheritance`.

.. [#f3] See section :ref:`sec:lexical-analyzer`.
