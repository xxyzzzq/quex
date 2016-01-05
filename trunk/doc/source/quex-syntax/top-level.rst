Top Level
=========

In this section 'top-level' syntax elements are discussed. Those are the syntax
elements which are not embedded inside others. Each such of them builds up a
syntactically independent unit. Each of them is presented together with the
ideas which are associated with it. There are two types of top level syntax
elements. First there are those which *configure functionality* of the analyzer
in some dedicated syntax. Second, there are those elements which plainly *paste
source* code into locations of the generated code. Each category is described
in its subsection.

Configuration
#############

The following item list outlines top-level syntax elements

.. data:: mode

   A mode section starts with the keyword ``mode`` and has the following syntax

   .. code-block:: cpp

      mode mode-name : 
           base-mode-1 base-mode-2 ...
           <tag-1> <tag-2> ...
      {
           pattern-1    action-1
           incidence-1  incidence-handler-1
           incidence-2  incidence-handler-2
           pattern-2    action-2
           pattern-3    action-3
           ...
      }

   The identifier following the ``mode`` keyword an names the mode to be
   specified.  Optional base modes and additional options, or 'tags', can be
   specified after a colon. A base mode list consists of a list of one or more
   white space separated names. Tags are bracketed in ``<`` and ``>``
   brackets. Mandatory for a mode is the section in curly brackets which
   follows. It defines pattern-action pairs and incidence handlers. Modes in
   itself are a subject that is described in its dedicated chapter
   :ref:`sec:modes`.


.. data:: define

   Definition of shorthands for patterns given as regular expressions [#f1]
   :reg:`sec:regular-expressions`.  The ``define`` keyword is followed by a
   section in curly brackets. The content of this section defines pattern
   names, shorthands, for patterns. 

   .. code-block:: cpp

      define {
          ...
          PATTERN_NAME    pattern-definition
          ...
      }

   This section is there for convenience. Regular expressions can get lengthy
   and hard to read. A pattern name ``my_pattern`` defined in this section can
   expands in any other regular expression to its definition by
   ``{my_pattern}``, i.e. by putting it into curly brackets.  The pattern
   names, themselves, do not enter any name space of the generated source code.
   They are only known inside the mode definitions. 

.. data:: token

   In this section token identifier can be specified. The definition of token
   identifiers is optional. The fact that Quex warns about undefined token-ids
   helps to avoid dubious effects of typos, where the analyzer sends token ids
   that no one catches.

   The syntax of this section is 

       .. code-block:: cpp

              token {
                  ...
                  TOKEN_NAME;
                  ...
              }
      
   The token identifiers need to be separated by semi-colons.

   .. note:: 

      The token identifier in this section are prefix-less. The token prefix, e.g. defined
      by comand line option ``--token-id-prefix`` is automatically pasted in front of the 
      identifier.

      .. code-block:: cpp

              repeated_token {
                  ...
                  TOKEN_NAME;
                  ...
              }

      Inside this section the token names are listed that may be sent via
      implicit repetition using ``self_send_n(...)``. That is, inside the token
      a repetition number is stored and the ``receive()`` function keeps
      returning the same token identifier until the repetition number is zero.
      Only tokens, that appear inside the ``repeated_token`` section may be
      subject to this mechanism.

.. data:: token_type

      Defines a token type other than the default token type. This feature is
      explained later in chapter :ref:`sec:token` where customized token types are
      discussed.

.. data:: repeated_token

      Specifies those token types which are subject to token repetition
      in notified through a repetition number inside the token itself.  It
      is discussed in section :ref:`sec:token-repetition`.

.. data:: start

    An initial mode ``START_MODE`` in which the lexical analyzer starts its
    analysis can be specified via 

    .. code-block:: cpp

       start = START_MODE;

Pasting Source Code
###################

Section which define code to be pasted into generated code follow the pattern::

       section-name {
           ...
           section content
           ...
       }

Whatever is contained between the two brackets is pasted in the corresponding location
for the given section-name. The available sections are the following:

.. data:: header

   Content of this section is pasted into the header of the generated files. Here, 
   additional include files may be specified or constants may be specified. 

.. data:: body

   Extensions to the lexical analyzer class definition. This is useful for 
   adding new class members to the analyzers or declaring ``friend``-ship
   relationships to other classes. For example:

   .. code-block:: cpp

        body {
                int         my_counter;
                friend void some_function(MyLexer&);
        }

   defines an additional variable ``my_counter`` and a friend function inside
   the lexer class' body.

.. data:: init

   Extensions to the lexical analyzer constructor. This is the place to initialize
   the additional members mentioned in the ``body`` section. Note, that as in every
   code fragment, the analyzer itself is referred to via the ``self`` variable. 
   For example

   .. code-block:: cpp

        init {
                self.my_counter = 4711;
        }

   Initializes a self declared member of the analyzer ``my_counter`` to 4711.

.. data:: reset

   Section that defines customized behavior upon reset. This fragment is
   executed after the reset of the remaining parts of the lexical analyser.
   The analyzer is referred to by ``self``.

Quex supports the inclusion of other files or streams during analysis. This
is done by means of a include stack handler :ref:`sec:include-stack`. It writes the
relevant state information into a so called *memento* [#f2]_ when it dives
into a file and restores its state from it when it comes back. The following
sections allow to make additions to the memento scheme of the include handler:

.. data:: memento

   Extensions to the memento class that saves file local data before a sub-file
   (included file) is handled.

.. data:: memento_pack

   Code to be treated when the state of a lexical analyzer is stored in a memento.

   Implicit Variables:

   ``memento``: Pointer to the memento object.

   ``self``: Reference to the lexical analyzer object.

   ``InputName``: Name of the new data source to be included. 
   
   The ``InputName`` may be a file name or any artificial identifier passed to one of 
   the include-push functions (:ref:`sec:include-stack`).

.. data:: memento_unpack

   Code to be treated when the state of a lexical analyzer is restored from a memento.

   Implicit Variables:

   ``memento``: Pointer to the memento object.

   ``self``: Reference to the lexical analyzer object.

.. rubric:: Footnotes

.. [#f1] Quex's regular expressions extend the POSIX regular expressions by queries 
         for unicode properties :ref:`sec:re-unicode-properties` and regular expression 
         algebra :ref:`sec:re-algebra`.

.. [#f2] File inclusion and return from file inclusion relates to freezing and unfreezing
         the current state of the analyzer. It is implemented by the so called 'Memento'
         desing pattern :cite:`Gamma1994design`.

