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

.. data:: <restrict: arg>

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


.. data:: on_entry

    Implicit Argument: ``FromMode``

    Incidence handler to be executed on entrance of the mode. This happens as a reaction 
    to mode transitions. ``FromMode`` is the mode from which the current mode
    is entered.

.. data:: on_exit

    Implicit Argument: ``ToMode``

    Incidence handler to be executed on exit of the mode. This happens as a reaction 
    to mode transitions. The variable ``ToMode`` contains the mode to which
    the mode is left.
    
.. data:: on_match

    Implicit Arguments: ``Lexeme``, ``LexemeL``, ``LexemeBegin``, ``LexemeEnd``

    This incidence handler is executed on every match that every happens while this
    mode is active. It is executed *before* the pattern-action is executed that is
    related to the matching pattern. The implicit arguments allow access to
    the matched lexeme and correspond to what is passed to pattern-actions.

.. data:: on_after_match

    Implicit Arguments: ``Lexeme``, ``LexemeL``, ``LexemeBegin``, ``LexemeEnd``

    The ``on_after_match`` handler is executed at every pattern match. It
    differs from ``on_match`` in that it is executed *after* the
    pattern-action. To make sure that the handler is executed, it is essential
    that ``return`` is never a used in any pattern action directly. If a forced 
    return is required, ``RETURN`` must be used. 

    .. warning::

        When using the token policy 'queue' and sending tokens from inside the 
        ``on_after_match`` function, then it is highly advisable to set the safety
        margin of the queue to the maximum number of tokens which are expected to
        be sent from inside this handler. Define::

               -DQUEX_SETTING_TOKEN_QUEUE_SAFETY_BORDER=...some number...
     
        on the command line to your compiler. Alternatively, quex can be passed the 
        command line option ``--token-policy-queue-safety-border`` followed by the
        specific number.

    .. note::

       Since ``on_after_match`` is executed after pattern actions have been done.
       This includes a possible sending of the termination token. When asserts
       are enabled, any token sending after the termination token may trigger 
       an error. This can be disabled by the definition of the macro::
       
                QUEX_OPTION_SEND_AFTER_TERMINATION_ADMISSIBLE 


.. data:: on_failure

   Incidence handler for the case that a character stream does not match any pattern 
   in the mode. This is equivalent to the ``<<FAIL>>`` pattern as known in 
   the 'lex' family of lexical analyzer generators. ``on_failure``, though, eats
   one character. The lexical analyzer may retry matching from what follows.

   .. note:: The definition of an ``on_failure`` section can be of great help
             whenever the analyzer shows an unexpected behavior. Before doing any
             in-depth analysis, or even bug reporting, the display of the mismatching
             lexeme may give a useful hint towards a lack in the specified pattern set.

   .. note:: The ``on_match`` and ``on_after_match`` handlers are not executed
             before and after the ``on_failure``. The reason is obvious, because 
             ``on_failure`` is executed because nothing matched. If nothing matched 
             then there is no incidence triggering ``on_match`` and ``on_after_match``.

   .. note:: Quex does not allow the definition of patterns which accept nothing.
             Actions, such as mode changes on the incidence of 'nothing has matched'
             can be implemented by ``on_failure`` and ``undo()`` as

             .. code-block:: cpp
              
                ...
                on_failure { self.undo(); self << NEW_MODE; }
                ...

             If ``undo()`` is not used, the letter consumed by ``on_failure`` is not
             available to the patterns of mode ``NEW_MODE``. In C, 

   In a broader sense, 'on_failure' implements the 'anti-pattern' of all
   occurring patterns in a mode. That is it matches the shortest lexeme that
   cannot match any lexeme in the mode. It is ensured, that the input is
   increased at least by one, so that the lexical analyzer is not stalled on
   the incidence of match failure.  In general, the non-matching characters are
   overstepped. If the analyzer went too fare, the 'undo' and 'seek' function
   group allows for precise positioning of the next input (see section ''stream
   navigation''). That the philosophy of ``on_failure`` is to catch flaws in 
   pattern definitions. If anti-patterns or exceptional patterns are to be 
   caught, they are best defined explicitly. 
   
   The definition of anti-patterns is not as difficult as it seems on the first 
   glance--the use of pattern precedence comes to help. If the interesting patterns
   are defined before the all-catching anti-pattern, then the anti-pattern can 
   very well overlap with the interesting patterns. The anti-pattern will only
   match if all preceding patterns fail.

   .. note::

      A lesser intuitive behavior may occur when the token policy 'queue'
      is used, as it is by default. As any other token which is sent, it goes
      through the token queue. It arrives at the user in a delayed manner after
      the queue has been filled up, or the stream ends. In this case, an
      immediate exceptional behavior cannot be implemented by the token passing
      and checking the token identifier. 

      To implement an immediate exception like behavior, an additional member
      variable may be used, e.g.

      .. code-block:: cpp

         body {
             bool   on_failure_exception_f;
         } 
         init {
             on_failure_exception_f = false;
         }
         ...
         mode MINE {
            ...
            on_failure { self.on_failure_exception_f = true; }
         }

      Then, in the code fragment that receives the tokens the flag could be
      checked, i.e.

      .. code-block:: cpp

         ...
         my_lexer.receive(&token);
         ...
         if( my_lexer.on_failure_exception_f ) abort();
         ...

   .. note::

      In cases where only parts of the mismatching lexeme are to be skipped,
      it is necessary to 'undo' manually. That is if one wants to skip only
      the first non-matching character all but one characters have to be 
      undone as shown below

      .. code-block:: cpp
         
         on_failure {
             QUEX_NAME(undo_n)(&self, LexemeL - 1);
             /* in C++: self.undo_n(LexemeL - 1) */
             self_send1(QUEX_TKN_FAILURE, Lexeme);
         }

.. data:: on_encoding_error

   When a converter or a encoding engine is used it is conceivable that the input
   stream contains data which is not a valid code point. To deal with that, the
   'on_encoding_error' handler can be specified.

.. data:: on_end_of_stream

   Incidence handler for the case that the end of file, or end of stream is reached.
   By means of this handler the termination of lexical analysis, or the return
   to an including file can be handled. This is equivalent to the ``<<EOF>>`` 
   pattern.

.. data:: on_skip_range_open

   Implicit Arguments: ``Delimiter`` [``Counter``]

   A range skipper skips until it find the closing delimiter. The event handler 
   ``on_skip_range_open`` handles the event that end of stream is reached before
   the closing delimiter. In case of a plain range skipper, the argument ``Delimiter``
   provides the string of the delimiter. For a nested range skipper the ``Counter``
   argument notifies additionally about the nesting level, i.e. the number of
   missing closing delimiters. Example:

       .. code-block:: cpp

          mode X : <skip_range: "/*" "*/"> { 
              ... 
          }

   skips over anything in between ``/*`` and ``*/``. However, if an analyzed
   file contains:

       .. code-block:: cpp

          /* Some comment without a closing delimiter


   where the closing ``*/`` is not present in the file, then the incidence
   handler is called on the incidence of end of file. The argument ``Delimiter`` 
   contains the string ``*/``.
      
There are incidence handlers which are concerned with indentation detection, in
case that the user wants to build indentation based languages. They are 
discussed in detail in section :ref:`_sec-advanced-indentation-blocks`. 
Here, there are listed only to provide in overview.

.. data:: on_indentation

    .. note:: Since version 0.51.1 this handler is very loosely supported since
              indentation management has been improved heavily. It is likely
              that it will be removed totally.

    The occurrence of the first non-white space in a line triggers the ``on_indentation``
    incidence handler. Note, that it is only executed at the moment where a pattern matches 
    that eats part (or all) of the concerned part of the stream. This incidence handler 
    facilitates the definition of languages that rely on indentation. ``Indentation``
    provides the number of white space since the beginning of the line. Please,
    refer to section :ref:`sec-advanced-indentation-blocks` for further information.

.. data:: on_indent

   If an opening indentation incidence occurs. 

.. data:: on_dedent

   If an closing indentation incidence occurs. If a line closes
   multiple indentation blocks, the handler is called *multiple*
   times.

.. data:: on_n_dedent

   If an closing indentation incidence occurs. If a line closes
   multiple indentation blocks, the handler is called only *once*
   with the number of closed domains.

.. data:: on_nodent

   In case that the previous line had the same indentation as the 
   current line.

.. data:: on_indentation_error

   In case that a indentation block was closed, but did not fit
   any open indentation domains.

.. data:: on_indentation_bad

   In case that a character occurred in the indentation which was
   specified by the user as being *bad*.

As it has been mentioned in many places before, incidence handlers are specified in
the same way like pattern-actions. 

