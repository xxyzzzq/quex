Precedence Rules 
----------------

Precise interpretation of data requires a distinct relation between data and
its meaning :cite:`Sproat2000computational`. For lexical analysis, this means
that relation between a stream of lexatoms and the stream of produced tokens
must be *distinct*. The input data is processed sequentially.  An analysis step
results in token sending and the increment of the input position.  Both are
accomplished as reactions to pattern matches. Consequently, to maintain a
distinct relation between the lexatom stream and the token stream, only one
pattern is allowed to match for a given position in the input. 

Patterns such as ``[0-9]+`` for numbers and ``[a-z]+`` for identifiers cannot
even partly match a common lexeme. Caution, however, is appropriate if the set
of matching lexemes intersects for two or more patterns--such as ``for`` and
``forest``.  Disambiguation, i.e. the determination of a single winning pattern
in case of multiple matches at the same stream position, is handled by match
precedence rules. The precedence rules are based on two attributes: The
*length* of the matching lexeme and the *position* of the matching pattern
inside the mode. Accordingly, the rules are:

  1. Longest Match: The pattern that matches the longest lexeme wins. 

  2. Highest Position: If two pattern match the exact same length, then 
     the position of the matching patterns decides. The pattern that
     comes first wins.
                     
The longest match rule implies, that if the two patterns ``for`` and ``forest``
are lurking, then ``forest`` wins if the input is "forester", for example. The
matching lexeme is "forest" and the next analysis step starts with "er". Both
patterns match, but the matching lexeme for ``forest`` is longer. The same is
true for post-contexts. If the patterns ``for`` and ``for/est`` were lurking,
then ``for/est`` would win with the matching lexeme "forester". The core
lexeme, though, is "for" and the next analysis step starts with "ester".

Two patterns may match the exact same lexeme. For example, given the two
patterns ``[a-z]+``, ``print``, and the input "print()", then the lexeme
"print" matches both patterns. In that case, the pattern wins which appears
first. If the patterns are located in different modes of an inheritance
hierarchy the pattern that comes first in the linearization wins.

Precedence Modifications
^^^^^^^^^^^^^^^^^^^^^^^^

The attribute *length* of matching lexeme is determined at run-time. So it
cannot be subject to predence modifications. However, the *position* of the
pattern may be adapted in a mode definition by two special commands. One
command allows to redefine the position of a base mode's pattern in the current
mode. The other command completely deletes a pattern. In both cases, 'DERIVED'
will behave differently from 'BASE' on patterns which are actually mentioned in
'BASE'. Using the commands formally breaks the 'is-a' relationship between
'DERIVED' and 'BASE'. Although, being hacky they are handy. The two commands
are the following:

.. data:: PRIORITY-MARK

    A pattern followed by this command is lifted into the current mode, thus having
    the priority according to the position in the current mode not of the base
    mode. The following example illustrates its usage with an 'identifier-keyword'
    problem. Mode 'BASE' defines how to match an identifier without considering
    possible intersections with keyword definitions, such as the keyword ``print``
    in 'DERIVED'.

    .. code-block:: cpp

        mode BASE {
          [a-z]+  => QUEX_TKN_IDENTIFIER(Lexeme); 
        }
        mode DERIVED : BASE {
          "print" => QUEX_TKN_KW_PRINT();
        }

    With this setup, the identifier pattern always matches. The code for the
    keyword ``print`` will never be executed, because ``[a-z]+`` matches the
    input "print" and comes first. Using ``PRIORITY-MARK``, though, the priority
    of the identifier pattern may be moved behind that of the keyword, so that 
    "print" can match and the identifier pattern's action is executed for all
    remaining identifiers. The usage is shown below.

    .. code-block:: cpp

        mode BASE {
          [a-z]+    => QUEX_TKN_IDENTIFIER(Lexeme); 
        }
        mode DERIVED : BASE {
          "print" => QUEX_TKN_KW_PRINT();
          [a-z]+  PRIORITY-MARK;
        }

   The ``PRIORITY-MARK`` for a pattern ``P`` re-prioritizes only patterns which
   have *higher priority* than ``P`` and are *identical* to ``P``. Higher
   priority means, that they were specified before ``P``. Identical means, that
   they match exactly the same set of lexemes as ``P`` does.

.. data:: DELETION

   The ``DELETION`` command implements a more brutal way to change the a
   pattern's priority. It completely delete the correspondent pattern-action
   pair in the current mode. In the following code fragment it is demonstrated
   how ``DELETION`` may be applied to solve the 'identifier-keyword' problem.

   .. code-block:: cpp

      mode BASE {
          [a-z]+  => TKN_IDENTIFIER(Lexeme);
      }
      mode B : A {
          [a-z]+  => DELETION; 
          print   => TKN_KW_PRINT(); 
      }

   The ``DELETION`` for a pattern ``P`` deletes only patterns which have a
   *higher priority* than ``P`` and are a *sub-pattern* to ``P``.  A pattern
   ``Q`` is a sub-pattern of ``P``, if ``P`` matches all lexemes which ``Q``
   possibly can match. 

It cannot be overemphasized that the modification of pattern precedences are
indicator for redesign. In particular, the ``DELETION`` command must be
considered only a temporary solution because of its drastic impact.


