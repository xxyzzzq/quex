*****
Modes
*****

A mode is a simplification where a set of behavior-related configurations is
associated with one distinct name: the mode name. A mode defines external and
internal behavior. That is, it defines *what* tokens may be produced and *how*
they are produced. A mode specifies the *interpretation* of an input stream but
also influences the *efficiency of interpretation*. 

This chapter elaborates on modes. It discusses mode transitions and mode
inheritance relationships. Pattern matching behavior is discussed in detail.
Incidences are discussed which are handled by dedicated handlers. Then, mode
tags (``<skip ...>``, ``<indentation ...>``, ...) are introduced. Eventually,
some light is shone on areas where vigilance is appropriate in order to avoid
unexpected behavior.

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
