
.. _sec:re-character-sets:

Character Set Expressions
==========================

Character set expressions are a tool to combine, filter and or select character
ranges conveniently. A resulting set of characters can then be used to express
that any of them may occur at a given position of the input stream. The
character set expression ``[:alpha:]``, for example matches all characters that
are letters, i.e. anything from `a` to `z` and `A` to `Z`. It belongs to the
POSIX bracket expressions :ref:`Burns2001real` which are explained below.
Further, this section explains how sets can be generated from other sets via
the operations *union*, *intersection*, *difference*, and *inverse*.

POSIX bracket expressions are basically shortcuts for some more regular
expressions that would formally look a bit more clumsy. The expressions and
what they stand for are shown in table :ref:`table:bracket-expressions`.

.. _table:bracket-expressions:

.. table::

    ==============  =================================  =====================================
    Expression      Meaning                            Related Regular Expression
    ==============  =================================  =====================================
    ``[:alnum:]``    Alphanumeric characters           ``[A-Za-z0-9]``                          
    ``[:alpha:]``    Alphabetic characters             ``[A-Za-z]``                             
    ``[:blank:]``    Space and tab                     ``[ \t]``                                
    ``[:cntrl:]``    Control characters                ``[\x00-\x1F\x7F]``                      
    ``[:digit:]``    Digits                            ``[0-9]``                                
    ``[:graph:]``    Visible characters                ``[\x21-\x7E]``                          
    ``[:lower:]``    Lowercase letters                 ``[a-z]``                                
    ``[:print:]``    Visible characters and spaces     ``[\x20-\x7E]``                          
    ``[:punct:]``    Punctuation characters            ``[!"#$%&'()*+,-./:;?@[\\\]_`{|}~]`` 
    ``[:space:]``    White space characters             ``[ \t\r\n\v\f]``                        
    ``[:upper:]``    Uppercase letters                 ``[A-Z]``                                
    ``[:xdigit:]``   Hexadecimal digits                ``[A-Fa-f0-9]``                          
    ==============  =================================  =====================================

Caution has to be taken if these expressions are used for non-english
character encodings. They are *solely* concerned with the ASCII character set. For more
sophisticated property processing it is advisable to use Unicode property
expressions as explained in section :ref:`sec:ucs-properties`. In particular,
it is advisable to use ``\P{ID_Start}``, ``\P{ID_Continue}``,
``\P{Hex_Digit}``, ``\P{White_Space}``, and ``\G{Nd}``.

.. note::

   If it is intended to use codings different from ASCII, e.g. UTF-8 or
   other Unicode character encodings, then the '--iconv' flag or '--icu'
   flag must be specified to enable the appropriate converter. See
   section :ref:`sec:character-encodings`.

Character sets do not related to state machines such as patterns do.
Nevertheless, they might be defined and expanded in ``define`` sections the
same way as regular expressions. Character set operations may then be applied
to sequentially described complex set descriptions. The available operations
correspond to those of *algebra of sets* :cite:`Quine1969set` and are listed in
table :ref:`table:character-set-operations`.

.. _table:character-set-operations:

.. table::

    ===============================  =====================================================
    Syntax                           Example
    ===============================  =====================================================
    ``union(A0, A1, ...)``            ``union([a-z], [A-Z]) = [a-zA-Z]``
    ``intersection(A0, A1, ...)``     ``intersection([0-9], [4-5]) = [4-5]`` 
    ``difference(A, B0, B1, ...)``    ``difference([0-9], [4-5]) = [0-36-9]``
    ``inverse(A0, A1, ...)``          ``inverse([\x40-\5A]) = [\x00-\x3F\x5B-\U12FFFF]`` 
    ===============================  =====================================================

A ``union`` expression allows to create the union of all sets mentioned inside
the brackets.  The ``intersection`` expression results in the intersection of
all sets mentioned. The difference between one set and another can be computed
via the ``difference`` function. Note, that ``difference(A, B)`` is not equal
to ``difference(B, A)``. This function takes more than one set to be
subtracted. In fact, it subtracts the union of all sets mentioned after the
first one. This is for the sake of convenience, so that one has to build the
union first and then subtract it. The ``inverse`` function builds the
complementary set. That is, the result is the set of characters which are not
in the given set but in the set of the currently considered encoding.  This
function also takes more than one set, so one does not have to build the union
first.

.. note::

    The ``difference`` and ``intersection`` operation can be used conveniently
    to filter different sets. For example

    .. code-block:: cpp

      [: difference(\P{Script=Greek}, \G{Nd}, \G{Lowercase_Letter} :]

    results in the set of Greek characters except the digits and except the
    lowercase letters. To allow only the numbers from the Arabic code block
    ``intersection`` can be used as follows:

    .. code-block:: cpp

      [: intersection(\P{Block=Arabic}, \G{Nd}) :]

The result of character set expressions is not always easy to foresee. Quex,
however, provides a command line functionality to display the results of
regular expressions. For example, the following command line displays what
characters remain if the numbers and lowercase letters are taken out of the set
of Greek letters.

.. code-block:: bash

   quex --set-by-expression 'difference(\P{Script=Greek}, \G{Nd}, \G{Lowercase_Letter})'

The command line query feature is discussed in a later chapter.  The subsequent
section elaborates on the concept of Unicode properties and how they may be
used to produce character sets.


