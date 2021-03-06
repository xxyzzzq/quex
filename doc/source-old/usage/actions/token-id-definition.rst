.. _sec-token-id-definition:

Token ID Definition
=====================

A token identifier is an integer that tells what type of lexeme has been
identified in the input stream. Those identifiers can either be referred to a
named constants that are prefixed with a so called token id prefix, or directly
with a number or a character code. 

All names of token identifiers must have the same prefix. The default
prefix is ``QUEX_TKN_``, but it can be also adapted using the command line
option ``--token-id-prefix`` followed by the desired prefix. A name space
of a token id definition may also be specified. For example

   > quex ... --token-id-prefix example::bison::token::

defines a prefix which consist of a name space reference. A call to quex 
with::

   > quex ... --token-id-prefix example::bison::token::TK_

specifies further, that only tokens in the given name space are considered
which start with ``TK_``. 

The token id constants do not have to be defined explicitly, but they can be
defined in a `token` section, such as in the following example:

.. code-block:: cpp

    token {
       IDENTIFIER;
       STRUCT;
       TYPE_INT;
       TYPE_DOUBLE;
       SEND;
       EXPECT;
       SEMICOLON;
       BRACKET_OPEN;
       BRACKET_CLOSE;
       NUMBER;
    }

Note, that the names of the token identifiers are specified without any prefix.
This reduces typing efforts and facilitates the change from one token prefix to
another.  The explicit definition of token identifiers has an advantage. If a
token identifier is mentioned in the `token` section, then quex will not report
a warning if it hits on a token identifier that is not defined in the token
section.  Imagine a typo in the description of pattern-action pairs:

.. code-block:: cpp

    ...
           "for"  => TKN_KEVWORB;   // typo: V <-> Y 
    ...

Assume that the writer of these lines intended to write ``TKN_KEYWORD``
and his code expects the token id to appear upon a detection of ``for``.
The token id ``TKN_KEVWORD`` contains a ``V`` instead of a ``Y`` 
and a dedicated token id is generated. The compiler compiles without complaints
but the token id ``TKN_KEYWORD`` is not received upon the detection
of ``FOR``. To avoid such confusion some effort was done so that Quex
would report on undefined token ids.

Numbers can be explicitly assigned to token ids using the general number
specification scheme (:ref:`sec-basics-number-format`). This allows for certain
'tricks'. For example, token id groups may be defined in terms of a signal bit,
e.g.

.. code-block:: cpp

   token { 
        TERMINATION   = 0b0000.0000;
        UNINITIALIZED = 0b1000.0000;
        DIV           = 0b0000.0001;
        MULTIPLY      = 0b0001.0001;
        PLUS          = 0b0011.0001;
        MINUS         = 0b0100.0001;
   }

By ensuring that only operators ``DIV``, ``MULTIPLY``, ``PLUS`` and ``MINUS``
contain bit zero, the test for an operator token can happen by a simple
binary 'and'

.. code-block:: cpp

   if( token_id & 0x1 ) {
       // 'token_id' is either DIV, MULTIPLY, PLUS, or MINUS 
       ...
   }

External Token ID Definitions
#############################

There is another way to define names of token identifiers. In frameworks with
automatic parser generators, it is common that the parser generator provides a
file with token identifier definitions. To handle this, quex accepts foreign
token id definition files. The goals of this option are

  (1) to enable Quex to warn about the usage of undefined token ids.

  (2) to ensure a consistent numeric implementation of token id names
      between the lexical analyzer engine and the caller in the code.

Quex is not aware of the numeric values of token ids. I collects only names
of token id constants. When a foreign token-id file is used *all* token ids
must be defined there. The ``token`` section may no longer be used. This
measure was taken to avoid any interference between Quex's auto-generated token-ids
and the specifications in the external token id definition file.

The foreign token id file can be specified by the ``--foreign-token-id-file``
command line option followed by the name of the file.  For example, if the
bison parser generator creates a token id file called ``my-token-ids.hpp`` Quex
might be called as follows

.. code-block:: bash

    > quex ... --foreign-token-id-file my-token-ids.hpp 

If the token ids there are specified in the namespace 'token::' and 
all have the prefix ``TK_`` the ``--token-id-prefix`` option must
be used additionally.

.. code-block:: bash

    > quex ... --foreign-token-id-file my-token-ids.hpp \
               --token-id-prefix       token::TK_

In case that a header contains definitions which may be confused with token id
definitions, the region in the file may be specified. This can be done with 
begin and end triggers as in the following example::

    > quex ... --foreign-token-id-file my-token-ids.hpp  yytokentype  '};' 

Then, the scanning of token ids starts with the line where ``yytokentype``
appears and ends with the next occurrence of '};'. In the following 
code fragment, only ``INTEGER`` and ``STRING`` will be considered.

.. code-block:: cpp

    namespace Example {
        namespace BisonicParser  {
            ...
            struct token
            {
                enum yytokentype {
                    INTEGER = 258
                    STRING  = 259
                };
            ...

Quex does not fully understand token id definition file in a way as a
C-Compiler does. For example, it does not handle C-pre-processor statements.
Practically, this could imply, that it considers token ids to be defined which
are not, or vice versa.  The fact that Quex refuses additional token id
definitions in the ``token`` section is enough to ensure consistency. The
consistent definition of token ids remains completely in the hands of
whatsoever writes the external token id file.

If one is interested to see what token ids where actually recognized from
the external token id definition file, then the option ``--foreign-token-id-file-show``
may be used. When applied to the aforementioned file, the output will be

.. code-block:: bash

    note: Token ids found in file 'my-token-ids.hpp' {
    note:     Example::BisonicParser::token::INTEGER => 'INTEGER'
    note:     Example::BisonicParser::token::STRING  => 'STRING'
    note: }

The name space to which the findings are attributed depends on what 
was passed to the option ``--token-id-prefix``.
