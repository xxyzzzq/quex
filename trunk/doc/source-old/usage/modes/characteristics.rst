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

.. data::   <inheritable: arg> 

   This option allows to restrict inheritance from this mode. Following values
   can be specified for ``arg``:
   
   * ``yes`` (which is the default value) explicitly allows to inherit from that mode. 
   
   * ``no`` means that no other mode may inherit from this mode. 
   
   * ``only`` prevents that the lexical analyzer ever enters this 
      mode. Its sole purpose is to be a base mode for other modes. It then 
      acts very much like an *abstract class* in C++ or an *interface* in Java.

.. data::  <exit: arg0 arg1 ... argN>      

   As soon as this option is set, the mode cannot be left except towards the 
   modes mentioned as arguments ``arg0`` to ``arg1``. If no mode name is specified
   the mode cannot be left. By default, the allowance of modes mentioned in the
   list extends to all modes which are derived from them. This behavior can 
   be influenced by the ``restrict`` option.

.. data::  <entry: arg0 arg1 ... argN>      

   As soon as this option is set, the mode cannot be entered except from the 
   modes mentioned as arguments ``arg0`` to ``arg1``. If no mode name is specified
   the mode cannot be entered. The allowance for inherited modes follows the scheme
   for option ``exit``.

.. data:: <restrict: arg> (No longer supported)

   Restricts the entry/exit admissions to the listed modes. Following settings for ``arg``
   are possible:

   * ``exit``: No mode derived from one of the modes in the list of an ``entry`` option is allowed automatically. 

   * ``entry``: Same as ``exit`` for the modes in the ``entry`` option.

.. data:: <skip: [ character-set ]>

   By means of this option, it is possible to implement optimized skippers for 
   regions of the input stream that are of no interest. White space for example
   can be skipped by defining a ``skip`` option like::

      mode MINE : 
      <skip:  [ \t\n]> {
          ...
      }

    Any character set expression as mentioned in <<section>> can be defined 
    in the skip option. Skipper have the advantage that they are faster than
    equivalent implementations with patterns. Further, they reduce the 
    requirements on the buffer size. Skipped regions can be larger than
    the buffer size. Lexemes need be smaller or equal the buffer size.

    What happens behind the scenes is the following: The skipper enters the 
    race as all patterns with a higher priority than any other pattern in the
    mode. If it matches more characters than all other patterns, then it wins
    the race and it enters the 'eating mode' where it eats everything until the
    first character appears that does not fall into the specified skip character
    set. Note, in particular that within a given mode

    .. code-block:: cpp

       mode X : <skip: [ \t\n] {
           \\\n  => QUEX_TKN_BACKLASHED_NEWLINE;
       }

    The token ``QUEX_TKN_BACKLASHED_NEWLINE`` will be sent as soon as the lexeme
    matches a backslash and a newline. The newline is not going to be eaten. If
    the skipper dominates a pattern definition inside the mode, then quex is 
    going to complain.

.. data:: <skip_range: start-re end-string>

   This option allows to define an optimized skipper for regions that are of no interest
   and which are determined by delimiters. In order to define a skipper for C/C++ comments
   one could write::

      mode MINE : 
      <skip_range:  "/*" "*/"> 
      <skip_range:  "//" "\n"> {
          ...
      }

   when the ``skip_range`` option is specified, there is an incidence handler
   available that can catch the incidence of a missing delimiter, i.e. if an end of
   file occurs while the range is not yet closed. The handler's name is
   ``on_skip_range_open`` as described in
   :ref:`_sec-usage-modes-characteristics-incidence-handlers`. The ``start-re``
   can be an arbitrary regular expression. The ``end-string`` must be a 
   linear string.

   .. warning:: For 'real' C++ comments the ``skip_range`` cannot produce a behavior
                that conforms to the standard. For this, the lexical analyzer must
                be able to consider the following as a single comment line

                .. code-block:: cpp

                   // Hello \ this \
                      is \
                      a comment

                where the end of comment can be suppressed by a backslash-ed followed
                by white space. The ``skip_range`` option's efficiency is based on the
                delimiter being a linear character sequence. For the above case a 
                regular expression is required.

    For more complex cases, such as a standard conform C++ comment skipping must be
    replaced by a regular expression that triggers an empty action.

    .. code-block:: cpp

            mode X { 
                ...
                "//"([^\n]|(\\[ \t]*\r?\n))*\r?\n      { /* no action */ }
                ...
            }

    In a more general form, the following scheme might be able to skip most conceivable
    scenarios of range skipping:

    .. code-block:: cpp

            mode X { 
                ...
                {BEGIN}([:inverse({EOE}):]|({SUPPRESSOR}{WHITESPACE}*{END}))*{END}    { /* no action */ }
                ...
            }

    In the C++ case the following definitions are required

    .. code-block:: cpp

            define { 
                BEGIN        //
                END          \r?\n
                EOE          \n
                WHITESPACE   [ \t]
                SUPPRESSOR   \\
            }

    Where ``EOE`` stands for 'end of end', i.e. the last character of the ``END`` pattern.


.. data::   <skip_nested_range: start-string end-string> 

   With this option nested ranges can be skipped. Many programming languages 
   do not allow nested ranges. As a consequence it can become very inconvenient
   for the programmer to comment out larger regions of code. For example, the
   C-statements 
   
   .. code-block:: cpp

         /* Compare something_else */
         if( something > something_else ) {        
             /* Open new listener thread for reception */
             open_thread(my_listener, new_port_n); 
         } else { 
             /* Close all listening threads. */
             while( 1 + 1 == 2 ) { /* Forever */
                 const int next_listener_id = get_open_listener();
                 if( next_listener_id == 0 ) break;
                 /* Request from thread to exit/return. */
                 com_send(next_listener_id, PLEASE_RETURN); 
             }
         }

   Could only be commented out by ``/*`` ``*/`` comments if all closing ``*/``
   are replaced by something else, e.g. ``*_/``. Thus
   
   .. code-block:: cpp

         /*
         /* Compare something_else *_/
         if( something > something_else ) {        
             /* Open new listener thread for reception *_/
             open_thread(my_listener, new_port_n); 
         } else { 
             /* Close all listening threads. *_/
             while( 1 + 1 == 2 ) { /* Forever *_/
                 const int next_listener_id = get_open_listener();
                 if( next_listener_id == 0 ) break;
                 /* Request from thread to exit/return. */
                 com_send(next_listener_id, PLEASE_RETURN); 
             }
         }
         */

   and the compiler might still print a warning for each ``/*`` that opens inside
   the outer comment. When the code fragment is de-commented, all ``*_/`` markers
   must be replaced again with ``*/``. 
   
   All this fuss is not necessary, if the programming language supports nested comments.
   Quex supports this with nested range skippers. When a nested range skip option such
   as::

      mode MINE : 
      <skip_nested_range:  "/*" "*/"> {
         ...
      }

   is specified, then the generated engine itself takes care of the 'commenting depth'.
   No comment range specifiers need to be replaced in order to include commented regions
   in greater outer commented regions.

   .. warning:: Nested range skipping is a very nice feature for a programming
      language.  However, when a lexical analyzer for an already existing language
      is to be developed, e.g.  'C' or 'C++', make sure that this feature is not
      used. Otherwise, the analyzer may produce undesired results.

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

