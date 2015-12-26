Inheritance
===========

In Object-Oriented Programming a derived class may use the capabilities of
its base class via *inheritance*. Analogously, if a quex mode is derived from
another mode it inherits the same way the characteristics of that other mode.
This promotes the following ideas:

#. A mode has somehow the character of a set or a category. If a set *B* is
   a subset of a set *A* then every element of *B* conforms to the constraints
   for being *A*, but has some special constraints for being in *B*.

   A mode ``B`` is being derived from a mode ``A``, then it contains all
   characteristics of ``A`` but also some special ones that are not implemented
   in ``A``. 

#. Characteristics that are shared between modes are programmed in one single 
   place. For example, all modes might show the same reaction on *End of File*.
   Thus the pattern-action pair concerned with it might best be placed in 
   a common base mode. This ensures that changes which effect multiple modes
   can be accomplished from one single place in the source code.


The mechanism of inheritance has certain rules. Those rules can be expressed
in terms of mode characteristics. Let mode ``B`` derived from mode ``A``, then
the following holds:

Pattern-Action Pairs

   * Mode ``B`` contains all pattern-action pairs of ``A``.

   * The pattern-action pairs of ``A`` have higher precedence than the 
     pattern-action pairs of ``B``. That is, if a lexeme matches a pattern
     in ``A`` and a pattern in ``B`` of the same length, the pattern 
     action of mode ``A`` is executed.

     This ensures that ``A`` imposes its character on ``B``. Conversely, any
     mode derived from ``A`` can be assumed to show a behavior described in ``A``.

   * For patterns that appear in ``B`` and ``A`` the pattern action for the
     pattern in ``A`` is executed. This is a direct consequence of the previous
     rule.

   .. note:: 

      As a general rule, it can be imagined that if ``B`` is derived from ``A``
      it is as if the pattern-action pairs of ``A`` are pasted in front of ``B``'s 
      pattern-action pairs itself.

   Alternatively, pattern-actions of ``B`` could have been executed after the 
   pattern-actions of ``A`` in case of interference. However, the decision
   of a brutal overruling was done because the high probability of creating 
   a mess. Imagine, a lexical analyzer engine sends multiple tokens as a 
   reaction to a pattern match. Further, the places where those tokens
   are send are not in one place, but distributed over multiple classes.
   Also, multiple concatenated mode transitions are very much prone to 
   end up in total confusion. This is why pattern actions in a base mode overrule
   pattern actions in the derived mode.

   There are possibilities to influence this behavior to be discussed in <<section>>.

Incidence Handlers

   * Incidence handlers in ``B`` are executed after incidence handlers of ``A``.

     Note, that incidence handlers are not expected to perform mode transitions (see 
     <<section>>) [#f1]_. Also, tokens that are send from inside incidence handlers
     are *implicit* tokens, thus it is expected that those tokens are not
     necessarily tied to concrete lexemes. These assumptions makes the brutal
     overruling of the base mode over derived mode meaningless. Incidence handlers
     of base mode and derived mode may be executed both without an inherent
     source of confusion.


Figure :ref:`(this) <fig-mode-inheritance>` shows an example where a mode ``B``
is derived from  mode ``A``. The mode ``B*`` represents the internal result of
the result of inheritance: patterns of the base mode *overrule* patterns of the derived mode,
incidence handlers of the base mode *precede* incidence handlers of the derived mode.

.. _fig-mode-inheritance:

.. image:: ../../figures/mode-inheritance.*
   :align: center
   :alt:   Mode inheritance.

.. toctree::

   multiple-inheritance.txt
   pattern-action-precedence.txt

.. rubric:: Footnotes

.. [#f1] An exception is ``on_indentation``. However, this incidence handler is best placed
         in a common base mode, so that all modes use the same indentation mechanism.

