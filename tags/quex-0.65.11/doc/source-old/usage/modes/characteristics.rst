Mode Characteristics
====================

The close relationship between a 'mode' and a 'mood' has been mentioned in
literature <<cite Knuth>>. This section elaborates on how the character
of a particular mode can be specified. Such a specification happens with
the following constructs:

  Options
   
     Options have the form::

         mode MINE :
             <key-word: argument_0 argument_1 ...> {
               ...
         }

     That is they are bracketed in '<' '>' brackets, start with a key-word for
     the option and possibly some optional arguments. Options follow the mode definition
     immediately. Options allow one to restrict mode transitions and inheritance
     relationships. Also, there are options that allow the implementation of
     optimized micro-engines to skip ranges.

  Pattern-Action Pairs

     See <<section ...>>.

  Incidence Handlers

     Incidence handlers allow one to express reactions to incidences immediately. Examples
     for incidences are *mode entrance*, *mode exit*, and *on indentation*. Incidence 
     handlers appear together with pattern-action pairs in the body of the mode
     definition. They have the form::

         mode MINE {
               on_indentation { 
                   ...
               }
         }

     Note, that the presence of incidence handlers enforces that patterns that 
     have the same shape as an incidence handler need to be defined in quotes.
     A pattern ``else`` can be defined conveniently 'as is', but a pattern
     ``on_indentation`` would have to be defined in quotes, since otherwise
     it would be considered to be an incidence hander definition.::

         mode MINE {
             ...
             else             => QUEX_TKN_KEYWORD_ELSE; 
             "on_indentation" => QUEX_TKN_KEYWORD_ON_INDENTATION; 
             ...
         }

The following sections elaborate on the concepts of options and incidence handlers.
Pattern-action pairs have been discussed in previous sections.

Options
-------

The possible options for modes to be specified are the following.

-- CUTC-- 

.. _sec-usage-modes-characteristics-incidence-handlers:

Incidence Handlers
--------------

This section elaborates on the incidence handlers which can be provided 
for a mode. Incidence handlers are specified like::

       incidence_handler_name { 
           /* incidence handler code */
       }

Some incidence handlers provide implicit arguments. Those arguments do not appear
in the incidence handler definition. The list of incidence handlers is the following:


-- CUT --

As it has been mentioned in many places before, incidence handlers are specified in
the same way like pattern-actions. 

