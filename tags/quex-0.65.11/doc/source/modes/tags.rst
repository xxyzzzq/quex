Tags
====

Previous sections elaborated on the most essential mode characteristics as they
are pattern-action pairs and incidence handlers. This section introduces mode
tags and what they accomplish. Mode tags follow the ':' in the mode definition 
after the base mode list, if there is any. Mode tags are specified in arrow 
brackets. The tag ``something`` in mode 'EXAMPLE' below demonstrates a typical
mode tag appearance.::

      mode EXAMPLE : BASE0 BASE1 BASE2 
         <some_tag: ...> 
      {
      } 

The following list may serve as explanation and reference of all available mode
tags.

.. dada:: <counter: ...>

   Specifies the line and column number counting behavior. This is discussed
   in detail in :ref:`line-and-column-counting`.

.. data:: <indentation: ...> 

   A mode that is equipped with this tag contains an indentation base scope 
   detection, i.e. the offset rule. An empty tag is enough. The ellipsis
   stands for possible definitions of indentation spaces, newlines, newline 
   suppressors, bad indentation characters, etc. Indentation based scopes
   are handled in a dedicated section (see :ref:`sec:indentation-scopes`).

.. data::   <inheritable: arg> 

   The tag ``inheritable`` has been discussed in section :ref:`sec:inheritance`.

.. data::  <exit: arg0 arg1 ... argN>      

.. data::  <entry: arg0 arg1 ... argN>      

   The tags ``entry`` and ``exit`` have been discussed :ref:`sec:transitions`.

.. data:: <skip: [ character-set ]>

    By means of this option, it is possible to implement optimized skippers for 
    regions of the input stream that are of no interest. White space for example
    can be skipped by defining a ``skip`` option like::

          mode MINE : 
          <skip:  [ \t\n]> {
              ...
          }

    Any character set expression as mentioned in :ref:`sec:re-character-sets`
    can be defined in the skip option. Skipper have the advantage that they are
    faster than equivalent implementations with patterns. Further, they reduce
    the requirements on the buffer size. Skipped regions can be larger than the
    buffer size. Lexemes need be smaller or equal the buffer size.

    What happens behind the scenes is the following: The skipper enters the 
    race as all patterns with a higher priority than any other pattern in the
    mode. If it matches more characters than all other patterns, then it wins
    the race and it enters the 'eating mode' where it eats everything until the
    first character appears that does not fall into the specified skip character
    set. Note, in particular that within a given mode

    .. code-block:: cpp

       mode X : <skip: [ \t\n]> {
           \\\n  => QUEX_TKN_BACKLASHED_NEWLINE;
       }

    The token ``QUEX_TKN_BACKLASHED_NEWLINE`` will be sent as soon as the lexeme
    matches a backslash and a newline. The newline is not going to be eaten. If
    the skipper dominates a pattern definition inside the mode and error message
    is issued.

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
   available that can catch the incidence of a missing delimiter, i.e. if an
   end of file occurs while the range is not yet closed. The handler's name is
   ``on_skip_range_open`` as described in
   :ref:`_sec-usage-modes-characteristics-incidence-handlers`. The ``start-re``
   can be an arbitrary regular expression. The ``end-string`` must be a linear
   string.

   .. note:: 
   
      The ``skip_range`` cannot produce a behavior that conforms to the C++
      standard. To be compliant a lexical analyzer must cope with the following
      as a line of comment

      .. code-block:: cpp

           // Hello \ this \
              is \
              a comment

      Characters cannot be exempted during a ``skip_range`` run, such as the
      newline is exempted above by backslash. A standard conform C++ comment
      skipping may be achieved by the pattern-action pair below.

      .. code-block:: cpp

            mode X { 
                ...
                "//"([^\n]|(\\[ \t]*\r?\n))*\r?\n   { }
                ...
            }

      The general form of a comment with exempted patterns is 

      .. code-block:: cpp

              {BEGIN}([:inverse({EOE}):]|({SUPPRESSOR}{WHITESPACE}*{END}))*{END}    { }

      where ``BEGIN`` is the opening pattern, ``EOE`` is the last character of the
      end delimiter, ``SUPPRESSOR`` is a pattern that prevents the end-delimiter 
      from delimiting, ``END`` is the end delimiter, and ``WHITESPACE`` is describes
      whitespace. 


.. data::   <skip_nested_range: start-string end-string> 

   A nested range skipper makes it easy to comment out regions that 
   already contain a comment. For example, to comment out a code 
   fragment in 'C' such as the following,

   .. code-block:: cpp

         some command;       /* Do something      */
         some other command; /* Do something else */

   all comment end-delimiters would have to be omitted, i.e. replaced
   by something like "*_/", so that they do not terminated the comment. 
   A nested skipper keeps track of the number of opened comments. With a
   specification as::

      mode MINE : 
      <skip_nested_range:  "/*" "*/"> {
         ...
      }

   the code fragment above could be commented out by placing the "/*" and "*/"
   before and behind it without having to change any delimiter.

   .. code-block:: cpp

         /* 
            some command;       /* Do something      */
            some other command; /* Do something else */
         */

   .. warning:: 
   
      Nested range skipping is a very nice feature for a programming language.
      However, when a lexical analyzer for an already existing language is to
      be developed, e.g.  'C' or 'C++', make sure that this feature is *not*
      used. Otherwise, the analyzer may not be standard compliant!

