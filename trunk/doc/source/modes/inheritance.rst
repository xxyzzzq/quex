Inheritance
===========

Inheritance has been introduced with the programming
language SIMULA :cite:`Nygaard1978development` and popularized by C++
:cite:`Ekendahl2006hardware`, :cite:`Stroustrup1994design`.  It describes a
relation between two classes which maintain an 'is-a' relationship [#f1]_. For
example, the set of cars and the set of vehhicles: Any car is a vehicle, but not
vice versa. In that sense, cars inherit general properties of vehciles, 
such as having a position, a speed and an acceleration. But car has properties
that not all vehicles have such as a motor or a trunk. 

If some classes 'Car', 'MotorBike', and 'Bicycle' are derived from class
'Vehicle' then some work may be spared if the derived classes use content that
has already been implemented for 'Vehicle'. Besides the advantage of code
reuse, inheritance is a means to express *commonality* in the base class and
*speciality* in the derived class. Inheritance for modes does not comprise
*subtyping* :cite:`Cook1989inheritance` as it does not provide *polymorphism*.
That is, if a mode 'A1' inherits from mode 'A', then 'A1' is not expected to
play seamlessly the role of 'A'. 

Inheritance lets a set of derived modes share characteristics in a base mode.
The following subsections elaborate on inheritance rules of those
characteristics, namely: pattern-action pairs, incidence handlers, skippers,
entry- and exit- permissions, and counters. Let the base mode be called 'BASE'
and the derived mode 'DERIVED'. 

-------------------------------
Inherited Mode Characteristics
-------------------------------

Pattern-Action Pairs
^^^^^^^^^^^^^^^^^^^^

Mode 'DERIVED' inherits, i.e. receives, all patter-action pairs of 'BASE'.  The
pattern-action pairs of 'BASE' have a higher precedence than those of
'DERIVED'.  If a lexeme matches a pattern in 'BASE' and a pattern in 'DERIVED'
of the same length, the pattern action of mode 'BASE' is executed.  The
behavior of pattern-action pairs in 'DERIVED' is as if the patterns of 'BASE'
were listed before the patterns of 'DERIVED'.  

If the exact same pattern appears in 'BASE' and 'DERIVED' an error is issued.
The same is true, if the exact same pattern appears in multiple base modes.

Patterns of a base class may be re-prioritized or even deleted using
``PRIORITY-MARK`` and ``DELETION`` (section :ref:`sec:match-precendence`).
However, they can only be considered workarounds, because with these two a
derived mode may actually behave completely different from its base mode. If
they are used, they are indicators for the need of mode structure redesign.


.. sec:incidence-handlers

Incidence Handlers
^^^^^^^^^^^^^^^^^^^^

Incidences handlers are *unique*. It is not allowed to have the same incidence
handler in 'DERIVED' and in 'BASE'. If an incidence handler was the aggregation
of shattered base class handlers, it would hardly be transparent what the
resulting code is actually doing. If an incidence handler in 'DERIVED' could
overwrite a handler in 'BASE', then 'DERIVED' could behave different from
what is expected from 'BASE'. This would break the 'is-a' relationship between
'DERIVED' and 'BASE'. The only possible conclusion is to make incidence handlers
unique and disallow for a derived class to re-define an incidence that has been
defined in one of the base modes.

Skippers
^^^^^^^^^^^^^^^^^^^^

Skippers are by their nature *aggregative*. In a single mode any number of
skipper definitions may occur. Adding skippers in 'DERIVED' only adds behavior
to what is expected from 'BASE'.

Entry- and Exit-Permissions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Entry- and exit-restrictions are inherited differently. Entry permissions are
aggregated *exclusively* and exit permissions are aggregated *inclusively*. If
a class specifies admissible entry modes, then only those modes are admissible
independent of the base modes. A single glance at the mode definition is enough
to perceive from where a mode can be entered--no further modes need to be
considered.  The exit modes of a class consists of the aggregation of all exit
modes of the base classes. To overview the exit permissions, all base modes
need to be considered.  However, this is necessary anyway since mode
transitions occur as reactions to pattern matches in the base modes and pattern
matches are collected inclusively upon inheritance.

.. note::

   Any pattern action exiting to a mode 'X' that is contained in a 'BASE' is
   present in 'DERIVED'. If 'DERIVED' was to disallow the exit to 'X', then it
   would contain a dysfunctional pattern action. Consequently, any desire to
   have an 'exclusive' inheritance behavior with respect to exit permissions
   solely indicates the necessity of a mode structure redesign.
   

Counters
^^^^^^^^^^^^^^^^^^^^

Counters are unique characteristics, if they are defined explicitly. It would
be counter-intuitive if to consider 'DERIVED' being some kind of 'BASE' while
it counts lines and columns differently.  If 'DERIVED' and 'BASE' define
counter schemes explicitly, then an error is issued.  The same is true, if two
base modes define a counter scheme.

Summary
^^^^^^^^^^^^^^^^^^^^

The introduced rules mainly maintain the 'is-a' relationship between 'DERIVED'
and 'BASE'. The inheritance rules are listed in table :ref:`table:inheritance`.
If inheritance cannot be applied because of these rules, it is a signal for the
need to redesign the mode structure. 

.. _table:inheritance:

.. table:: Inheritance Rules

    +------------------------+-------------------+--------------------------------------+
    | Characteristic         | Inheritance Rule  | Syntax                               |
    +========================+===================+======================================+
    | Pattern-Action Pairs   | aggregation       | Regular Expression                   |
    +------------------------+-------------------+--------------------------------------+
    | Skippers               | aggregation       | ``<skip:              ...>``         |
    +------------------------+-------------------+--------------------------------------+
    |                        |                   | ``<skip_range:        ...>``         |
    +------------------------+-------------------+--------------------------------------+
    |                        |                   | ``<skip_nested_range: ...>``         |
    +------------------------+-------------------+--------------------------------------+
    | Counters               | unique            | ``<counter: ...>``                   |
    +------------------------+-------------------+--------------------------------------+
    | Exit-Permission        | aggregation       | ``<exit: ...>``                      |
    +------------------------+-------------------+--------------------------------------+
    | Entry-Permission       | overwrite         | ``<entry: ...>``                     |
    +------------------------+-------------------+--------------------------------------+
    | Incidence Handlers     | unique            | ``on_after_match``                   |
    +------------------------+-------------------+--------------------------------------+
    |                        |                   | ``on_dedent``                        |
    +------------------------+-------------------+--------------------------------------+
    |                        |                   | ``on_bad_lexatom``                   |
    +------------------------+-------------------+--------------------------------------+
    |                        |                   | ``on_end_of_stream``                 |
    +------------------------+-------------------+--------------------------------------+
    |                        |                   | ``on_entry``                         |
    +------------------------+-------------------+--------------------------------------+
    |                        |                   | ``on_exit``                          |
    +------------------------+-------------------+--------------------------------------+
    |                        |                   | ``on_failure``                       |
    +------------------------+-------------------+--------------------------------------+
    |                        |                   | ``on_indent``                        |
    +------------------------+-------------------+--------------------------------------+
    |                        |                   | ``on_indentation``                   |
    +------------------------+-------------------+--------------------------------------+
    |                        |                   | ``on_indentation_bad``               |
    +------------------------+-------------------+--------------------------------------+
    |                        |                   | ``on_indentation_error``             |
    +------------------------+-------------------+--------------------------------------+
    |                        |                   | ``on_match``                         |
    +------------------------+-------------------+--------------------------------------+
    |                        |                   | ``on_n_dedent``                      |
    +------------------------+-------------------+--------------------------------------+
    |                        |                   | ``on_nodent``                        |
    +------------------------+-------------------+--------------------------------------+
    |                        |                   | ``on_nodent``                        |
    +------------------------+-------------------+--------------------------------------+
    |                        |                   | ``on_skip_range_open``               |
    +------------------------+-------------------+--------------------------------------+

If a mode solely serves as a definition of commonality for derived modes, then
there is no need to generate code for it. The mode itself will never be
entered. The redundant code generation can be avoided by means of the
``<inheritable: OPTION>`` tag. The ``OPTION`` can be one of the three

   * ``yes``: The mode can be used as base mode and it is also implemented.  This is the default setting. 

   * ``only``: The mode can only serve as a base mode. It is *not* implemented.

   * ``no``: The *cannot* serve as a base mode, but it is implemented.

.. note::

    A first approach to mode structure redesign in case of obstructed
    inheritance is the base mode split.  If mode 'DERIVED' needs something from
    'BASE', but it cannot derive from it, then 'BASE' may be split into two
    modes: 'BASE_CORE' which contains what 'DERIVED' requires. A second mode
    'BASE' may inherit from 'BASE_CORE' and implement what is missing from the
    original 'BASE' mode.  Then 'DERIVED' can inherit 'BASE_CORE'.

    For example, let 'BASE' implement a skipper that all modes shall share and
    handlers for ``on_failure`` and ``on_end_of_stream``. Mode 'DERIVED' might
    want to send a different termination token. This is impossible for a
    derived mode (see section :ref:`sec:incidence-handlers`).

    .. code-block:: cpp

       mode BASE : <skip: [ \t\n]+> {
           on_failure       => QUEX_TKN_FAILURE();
           on_end_of_stream => QUEX_TKN_TERMINATION();
       }

    If the base mode splits, it is still available for other modes as a base
    for derivation. However, a lighter version of it can be the base mode for
    'DERIVED' if there was no ``on_end_of_stream`` handler. The mode split is
    then implemented as

    .. code-block:: cpp

       mode BASE_CORE : <skip: [ \t\n]+> {
           on_failure => QUEX_TKN_FAILURE();
       }

       mode BASE : BASE_CORE {
           on_end_of_stream => QUEX_TKN_TERMINATION();
       }

    With the base modes split, 'DERIVED' can now be properly placed into the
    mode hierarchy--maximizing code reuse and displaying levels of
    generalization.


--------------------
Multiple Inheritance
--------------------

Multiple inheritance :cite:`Meyer1988object`, i.e. the derivation from more
than one base mode, is permitted. If modes were only to inherit one base mode,
then the pattern position, and therefore its precedence, would be trivial to
determine. Base mode patterns can be imagined to be pasted in front of the
current mode's patterns. Repeating this results in a linear chain of patterns.
Multiple inheritance, though, results in a mode tree. The mechanism to align
mode characteristics in multiple inheritance scenarios is discussed in the
subsequent paragraphs. 

Let the term 'sibling modes' mean a set of modes that appear on the same level
of inheritance.  The sequence of collecting mode characteristics in a mode tree
is controlled by the following rules:

    #. The precedence of sibling modes depends on the sequence that
       they are specified.

    #. Base modes have precedence over sibling modes. 
       
    #. No mode is treated twice.

To investigate those principles the following example of a mode structure may
be considered, where a mode 'A' is constructed from a complex inheritance tree. 

.. code-block:: cpp

    mode A : B, C     { [a-z]{1,9} => T_A(Lexeme); }
    mode B : D, E     { [a-z]{1,5} => T_B(Lexeme); }
    mode D : H        { [a-z]{1,2} => T_D(Lexeme); }
    mode H            { [a-z]{1,1} => T_H(Lexeme); }
    mode C : E, F, G  { [a-z]{1,8} => T_C(Lexeme); }
    mode G            { [a-z]{1,7} => T_G(Lexeme); }
    mode F            { [a-z]{1,6} => T_F(Lexeme); }
    mode E : I,       { [a-z]{1,4} => T_E(Lexeme); }
    mode I            { [a-z]{1,3} => T_I(Lexeme); }

The inheritance tree is displayed in :ref:`fig:multiple-inheritance`. The
letters in the boxes name the modes and the numbers at their right bottom edges
indicate the mode's precedence. According to rule 1, the base mode 'B' has a
higher precedence then 'C', because it is mentioned before it in the
definition. According to rule 2, base modes are considered before sibling
modes. Thus, one dives first into the direction of 'B'. Following these rules,
finally, mode 'H' is reached which is the first mode to be considered. Its
patterns have the highest precedence.  'H' has no sibling, so one goes up in
the hierarchy. 'D' has the second highest precedence. One level up, mode 'B' is
reached where 'D' has the sibling 'E'.  Diving down the 'E' branch one reaches
'I', which has the third highest precedence, etc.

.. _fig:multiple-inheritance:

.. image:: ../figures/mode-multiple-inheritance.*
   :align: center
   :alt:   Multiple inheritance mode structure.

Multiple inheritance implies the potential of the *diamond problem*
:cite:`Taivalsaari1996notion`.  In figure :ref:`fig:multiple-inheritance` the
modes 'A', 'B', 'C', and 'E' constitute such a 'diamond'. It is potentially
unclear whether 'E' is preceded by 'B' or by 'C' and if 'B' comes before 'C' or
vice versa. With the aforementioned three rules, however, this problem is
solved. 'B' is mentioned before 'C'. Diving down on 'B' one reaches 'E'. 
Then, elements of 'B' are collected. Next, one dives down the sibling 'C' but
reaches 'E' which by rule 3 cannot be considered any more. It remains to
collect the content of 'C' before collecting the content of 'A'. Thus, from the
contents of the modes 'A', 'B', 'C', and 'E', the content of 'E' has the highest
precedence, then that of 'B', then that of 'C', and then that of 'A'.

In any case, is is advisable when working with multiple inheritance, to have a
look at the documentation string that is produced produces about the
pattern-action pairs in the generated engine source file. The aforementioned
example caused quex to produce the following documentation::

    /* MODE A:
     ...
     *     PATTERN-ACTION PAIRS:
     *       ( 75) H: [a-z]{1,1}
     *       ( 76) D: [a-z]{1,2}
     *       ( 77) I: [a-z]{1,3}
     *       ( 78) E: [a-z]{1,4}
     *       ( 79) B: [a-z]{1,5}
     *       ( 80) F: [a-z]{1,6}
     *       ( 81) G: [a-z]{1,7}
     *       ( 82) C: [a-z]{1,8}
     *       ( 83) A: [a-z]{1,9}
     ...

The first column of the table gives the index that was created for the pattern.
It is an expression of precedence.  The second column tells from what mode the
pattern was inherited and the third column displays the pattern itself.

.. rubric:: Footnotes

.. [#f1] An 'is-a' relationship implements the *Liskov Substitution Principle*
        :cite:`Liskov1987KAD`. That is, let S be a subtype of T. Then, if a property is
        true for all elements in T, then the property must also be be true for all
        elements in S.
