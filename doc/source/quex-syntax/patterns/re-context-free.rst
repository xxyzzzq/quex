.. _sec:re-context-free:

Context Free Regular Expressions
==================================

Context free regular expressions match  against an input independent on what
comes before or after it.  Context-free-ness means, for example, that the
regular expression ``for`` will match against the letter sequence `f`, `o`, and
`r` independent of what comes before or after it.  Pre- and post-context for
pattern matching are explained in the subsequent section. 

.. describe:: x 

     matches the character 'x'.  That means, characters match simply the
     character that they represent.  This is true, as long as those characters
     are not part of the set of syntactic operators--such as ``.``, ``[``, 
     and  ``]``.

.. describe:: . 

     (is a syntactic operator) The dot matches any character in the current
     encoding except for the buffer limit code and '0x0A' for newline.  On
     systems where newline is coded as '0x0D, 0x0A' this does match the '0x0D'
     character whenever a newline occurs.

.. describe:: [xyz]

     a "character class" or "character set"; in this case, the pattern matches
     either an ``x``, a ``y``, or a ``z``.  Character sets specify an
     *alternative* expression for a single character.  If the brackets ``[``
     and ``]`` are to be matched quotes or backslashes have to be used.

.. describe:: [:expression:]

     matches a set of characters that result from a character set expression
     `expression`. Section :ref:`sec:re-character-sets` discusses this feature
     in detail.  In particular ``[:alnum:]``, ``[:alpha:]`` and the like are
     the character sets as defined as POSIX bracket expressions.

.. describe:: [abj-oZ]

     a "character class" with a range in it; matches an ``a``, a ``b``, any
     letter from ``j`` through ``o``, or a ``Z``. The minus ``-`` determines
     the range specification. Its left part is the start of the range.  Its
     right part is the end of the range (here ``j-o`` means from ``j`` to
     ``o``).  The ``-`` stands for 'range from to' where the character code 
     of the right hand side needs to be greater than the character code of 
     the left hand side.

.. describe:: [^A-Z\\n]

     a "negated character class", i.e., any character but those in the class.
     The ``^`` character indicates *negation* at this point.  This expression
     matches any character *except* an uppercase letter or newline.

.. describe:: "[xyz]\\"foo"

     matches the literal string: ``[xyz]"foo``.  Any character, that is not
     backslash or backslash proceeded is applied in its original sense. A ``[``
     stands for code point 91 (hex.  5B), matches against a ``[`` and does not
     mean 'open character set'. Inside strings ANSI-C backslash-ed characters
     ``\n``, ``\t``, etc. can be used. The quote can be specified by ``\"``.
     The Unicode property ``\N{...}`` is also available since it results in a
     *single character*. However, other operators such as ``\P{....}`` result
     in *character sets*. They cannot be used inside strings.
      
.. describe:: \\C{ R } or \\C(flags){ R }

     Applies case folding for the given regular expression or character set 'R'.
     This basically provides a shorthand for writing regular expressions that
     need to map upper and lower case patterns, i.e.::

           \C{select} 

     matches for example:: 

           "SELECT", "select", "sElEcT", ...

     The expression ``R`` passed to the case folding operation needs to fit 
     the environment in which it was called. If the case folding is applied
     in a character set expression, then its content must be a character
     set expression, i.e.::

               [:\C{[:union([a-z], [ﬀİ]):]}:]   // correct
               [:\C{[a-z]}:]                    // correct

     and *not*::

               [:\C{union([a-z], [ﬀİ])}:]       // wrong
               [:\C{a-z}:]                      // wrong

     The algorithm for case folding follows Unicode Standard Annex #21 
     "CASE MAPPINGS", Section 1.3. That is for example, the character 'k'
     is not only folded to 'k' (0x6B) and 'K' (0x4B) but also to 'K' (0x212A). 
     Additionally, Unicode defines case foldings to multi character sequences,
     such as::

            ΐ   (0390) --> ι(03B9)̈(0308)́(0301)
            ŉ   (0149) --> ʼ(02BC)n(006E)
            I   (0049) --> i(0069), İ(0130), ı(0131), i(0069)̇(0307)
            ﬀ   (FB00) --> f(0066)f(0066)
            ﬃ   (FB03) --> f(0066)f(0066)i(0069)
            ﬗ   (FB17) --> մ(0574)խ(056D)

     As a speciality of the Turkish language, the 'i' with and without the dot
     are not the same. That is, a dot-less lowercase 'i' is folded to a dot-less 
     uppercase 'I' and a dotted 'i' is mapped to a dotted uppercase 'I'. This 
     mapping, though, is mutually exclusive with the 'normal' case folding and 
     is not active by default. The following flags can be set in order to
     control the detailed case folding behavior:

     .. describe:: s

        This flag enables simple case folding *without* the multi-character

     .. describe:: m

        The *m* flag enables the case folding to multi-character sequences.
        This flag is not available in character set expressions. In this
        case the result must be a set of characters and not a set of character
        sequences.

     .. describe:: t

        By setting the *t* flag, the turkish case mapping is enabled. Whenever
        the turkish case folding is an alternative, it is preferred.
    
     The default behavior corresponds to the flags *s* and *m* 
     (``\C{R}`` ≡ ``\C(sm){R}``) for patterns and *s* (``\C{R}`` ≡ ``\C(s){R}``) 
     for character sets. Characters that are beyond the scope of the current 
     encoding or input character byte width are cut out seamlessly. 

.. describe:: \\R{ ... }

     Reverse the pattern specified in brackets. If for example, it is
     specified::

            "Hello "\R{dlroW} => QUEX_TKN_HELLO_WORD(Lexeme)

     then the token ``HELLO_WORLD`` would be sent upon the appearance of 
     'Hello World' in the input stream. This feature is mainly useful for
     definitions of patterns of right-to-left writing systems such 
     as Arabic, Binti and Hebrew. Chinese, Japanese, as well as ancient 
     Greek, ancient Latin, Egyptian, and Etruscan can be written in 
     both directions.

     .. note:: 

        For some reason, it has caused some confusion in the past, that pattern
        substitution requires an extra pair of curly brackets, i.e. to reverse
        what has been defined as ``PATTERN`` it needs to to be written::

                          \R{{PATTERN}} 

        which reads from inside to outside: expand the pattern definition,
        then reverse expanded pattern. Inside the curly brackets of ``\R{...}``
        any pattern expression may occur in the well defined manner.

.. describe:: \\A{P}

     Briefly worded, an anti-pattern of a pattern ``P`` matches all lexemes
     which are caught by a match failure of ``P``. 

     Let s(L) be a transformation which extracts out 'shortest' alternatives.
     Let Lx be the set of *x* from L for which there is a second lexeme *y* in L
     that starts with *x*. Then,::

                                 s(L) := L - Lx 
     
     As a result it is safe to assume that in s(L) there are no two lexemes
     *x* and *y* so that *x* is the start of *y*. For example, the pattern 
     '(ab)|(abc)' is matched by "ab" and "abc". The latter starts with the
     former. The transformation s((ab)|(abc)) takes out the longest 
     and matches therefore only "ab".

     Anti-Pattern
        Let Q be the set of all lexemes which are not matched by P. Let
        s(R) be the pattern that matches shortest alternatives in R. Then, the
        anti-pattern of P is the pattern which matches the set of lexemes
        given by 's(Q)'.

     .. _fig-anti-pattern-0:
 
     .. figure:: ../../figures/anti-pattern-0.png
 
        State machine matching the pattern ``for``.
 
     .. _fig-anti-pattern-1:
 
     .. figure:: ../../figures/anti-pattern-1.png
 
        State machine implementing the match of pattern ``\A{for}``.

     Figures :ref:`fig-anti-pattern-0` and :ref:`fig-anti-pattern-1` show the 
     state machines for matching the pattern ``for`` and ``\A{for}``. These 
     illustrations demonstrate that the anti-pattern does not match all 
     patterns which are not matched by ``for``. Instead, it matches a 
     'shortest subset'.
   
     Anti-patterns are especially useful for post contexts 
     (section :ref:`sec-pre-and-post-conditions`) and to implement shortest 
     match behavior with a greedy match analyzer engine 
     (section :ref:`usage-context-free-pitfalls`).

     .. note::

        If it is necessary to ensure that only one character is matched in 
        case of failure of all other patterns, then it is best to rely on the
        '.' specifier--as explained above.

.. describe:: \\0 

     a NULL character (ASCII/Unicode code point 0). This is to be used with
     *extreme caution*!  The NULL character is also used a buffer delimiter!
     See section :ref:`sec:formal-command-line-options` for specifying a different
     value for the buffer limit code.

.. describe:: \\U11A0FF 

     the character with hexadecimal value 11A0FF. A maximum of *six*
     hexadecimal digits can be specified.  Hexadecimal numbers with less than
     six digits must either be followed by a non-hex-digit, a delimiter such as
     ``"``, ``[``, or ``(``, or specified with leading zeroes (i.e. use
     \\U00071F, for hexadecimal 71F). The latter choice is probably the best
     candidate for an 'established habit'. Hexadecimal digits can contain be
     uppercase or lowercase letters (from A to F).

.. describe:: \\X7A27 

     the character with hexadecimal value 7A27. A maximum of *four*
     hexadecimal digits can be specified. The delimiting rules are are
     analogous to the rules for `\U`. 

.. describe:: \\x27 

    the character with hexadecimal value 27. A maximum
    of *two* hexadecimal digits can be specified. The
    delimiting rules are are analogous to the rules for `\U`. 

.. describe:: \\123 

    the character with octal value 123, a maximum of three
    digits less than 8 can follow the backslash. The
    delimiting rules are analogous to the rules for `\U`. 


.. describe:: \\a, \\b, \\f, \\n, \\r, \\t, \\r, or \\v

    the ANSI-C interpretation of the backslash-ed character.

.. describe:: \\P{ Unicode Property Expression }

     the set of characters for which the `Unicode Property Expression` holds.
     Note, that these expressions cannot be used inside quoted strings.

.. describe:: \\N{ UNICODE CHARACTER NAME }

     the code of the character with the given Unicode character name. This is 
     a shortcut for ``\P{Name=UNICODE CHARACTER NAME}``. For possible
     settings of this character see :cite:`Unicode2015`.

.. describe:: \\G{ X }

     the code of the character with the given *General Category* \cite{}. This is 
     a shortcut for ``\P{General_Category=X}``. Note, that these expressions 
     cannot be used inside quoted strings. For possible settings of the 
     ``General_Category`` property, see section :ref:`sec-formal-unicode-properties`.

.. describe:: \\E{ Codec Name }

     the subset of Unicode characters which is covered by the given encoding.
     Using this is particularly helpful to cut out uncovered characters when a
     encoding engine is used (see :ref:`sec:engine-encoding`).

Any character specified as character code, i.e. using `\`, `\x`, `\X`, or `\U`
are considered to be Unicode code points. For applications in English spoken
cultures this is identical to the ASCII encoding. For details about Unicode
code tables consider the standard :ref:`Unicode50`. Section
:ref:`sec:ucs-properties` gives an overview over the Unicode property system.

Two special expressions are due to the tradition of lex/flex. In Quex's 
terminology they are actually event handlers. They are still present in 
recognition of history and can only be used in the ``mode`` section:

.. describe:: <<EOF>> 

    the incidence of an end-of-file (end of data-stream) it is a 
    synonym for the incidence handler ``on_end_of_stream``. 

.. describe:: <<FAIL>> 

    the incidence of failure, i.e. no single pattern matched. It is 
    a synonym for ``on_failure``.

The incidence handlers ``on_end_of_stream`` and ``on_failure`` are explained in
section :ref:`sec:incidence-handlers`.

.. note::

   The space character (UCS 32) is not allowed except in quotes or in range
   boundaries. In fact, it is supposed to separate the pattern from subsequent
   tokens such as ``=>``. Also, it cannot be backslash-ed.
   
   The backslash also does not suppress newline. A pattern must be completely
   specified in a single line. The ``define`` section may be used to break
   down patterns into smaller ones and combine them by expansion.

*Operations*    

Let ``R`` and ``S`` be regular expressions, i.e. a chain of characters
specified in the way mentioned above, or a regular expression as a result from
the operations below.  Much of the syntax is directly based on POSIX extended
regular expressions.
     
.. describe:: R* 

    *zero* or more occurrences of the regular expression ``R``.

.. describe:: R+ 

    *one* or more repetition of the regular expression ``R``.

.. describe:: R? 

    *zero* or *one* ``R``. That means, there maybe an ``R`` or not.

.. describe:: R{2,5} 

    anywhere from two to five repetitions of the regular expressions ``R``.

.. describe:: R{2,} 

    two or more repetitions of the regular expression ``R``.

.. describe:: R{4} 

    exactly four repetitions of the regular expression ``R``.

.. describe:: (R) 

    match an ``R``; parentheses are used to *group* operations, i.e. to override
    precedence, in the same way as the brackets in ``(a + b) * c``
    override the precedence of multiplication over addition.

.. describe:: RS 

    the regular expression ``R`` followed by the regular expression ``S``. This
    is usually called a *concatenation* or a *sequence*.

.. describe:: R|S 

    either an ``R`` or an ``S``, i.e. ``R`` and ``S`` both match. This is usually 
    called an *alternative*.

.. describe:: {NAME} 

    the expansion of the defined pattern "NAME". Pattern names can
    be defined in *define* sections (see section :ref:`sec:top-level-configuration`).

