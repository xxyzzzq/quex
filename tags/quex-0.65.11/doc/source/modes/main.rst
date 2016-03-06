*****
Modes
*****

A mode is a simplification where a set of behavior-related configurations is
associated with one distinct name: the mode name. A mode defines external and
internal behavior. That is, it defines *what* tokens may be produced and *how*
they are produced. A mode specifies the *interpretation* of an input stream but
also influences the *efficiency of interpretation*. 

This chapter elaborates on modes. It discusses mode transitions. It shows
how mode inheritance may be used to transparently construct complex modes from
smaller base modes [#f1]_ . Pattern matching behavior is investigated in
detail.  Incidences are introduced which are handled by dedicated handlers.
Then, mode tags (``<skip ...>``, ``<indentation ...>``, ...) are listed and
explained.  Eventually, some light is shone on areas where vigilance is
appropriate in order to avoid unexpected behavior.

 #. transitions

 #. inheritance -> hierarchie
    <inheritable: ...>

 #. match precedence:
     #. length, pattern position, pattern position by base mode
     #. PRIORITY-MARK, DELETION-MARK
 
 #. incidence handlers

 #. tags
     #. <inheritable: >
     #. <exit >
     #. <entry >
     #. <skip, skip_range, skip_nested_range>
     #. <counter>
     #. <indentation>

 #. pitfalls
     #. regular expression pitfalls
     #. incidence handlers

.. toctree::

   transitions.rst
   inheritance.rst
   matching/main.rst 
   incidence-handlers.rst
   tags.rst
   pitfalls/main.rst


.. rubric:: Footnotes

.. [#f1] The *start conditions* in lex/flex :cite:`Paxson1995flex` are similar 
         to modes in a sense that they conditionally activate pattern matching 
         rules. However, lex does not provide a means to model inheritance 
         relationships between modes. The 'inclusiveness' of a mode in lex is 
         only related to rules without any start condition. 


