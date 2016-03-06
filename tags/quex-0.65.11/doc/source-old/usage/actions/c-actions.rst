.. _sec:c-code-fragments:

C/C++ Code Segments
===================

Alternatively to the convenient definition of actions in terms of sending tokens
and mode transition, more sophisticated behavior can be specified by inserting
code fragments directly as pattern-actions or incidence handlers. The syntax for 
such definitions is simply to enclose the code in curly brackets as in the following
example 

.. code-block:: cpp

    mode SOMETHING {
        ...

        "\"" {
            self << STRING_READER; 
            self_send(QUEX_TKN_EVENT_MODE_CHANGE);
            RETURN;
        }

        ...

        [a-z]+ {
            self_send(QUEX_TKN_IDENTIFIER, Lexeme);
            self.allow_opening_indentation_f = true;
            RETURN;
        }
    }

The C-code fragments may be ended with ``RETURN`` and ``CONTINUE``. If
``RETURN`` is specified the analyzer returns from its analysis. If ``CONTINUE``
is specified the analysis may continue without returning to the caller. The reason
for these two being defined as macros is that they behave differently depending
of token passing policies (:ref:`sec-token-policies`).

The functions used in this example are as follows. The lexical analyzer object
can be accessed via

.. data:: self

   self is a reference to the analyzer inside pattern actions and incidence handlers.

The following send macros are available:

.. cfunction:: self_send(TokenID)

    Sends one token to the caller of the lexical analyzer with the given 
    token identifier ``TokenID``.

.. cfunction:: self_send_n(N, TokenID)

    Implicit repetition of tokens can be achieved via the ``self_send_n``
    macro. The token identifiers to be repeated must be defined in the
    ``repeated_token`` section, i.e.

       .. code-block:: cpp

          repeated_token {
              BLOCK_CLOSE;
              BRACKET_OPEN;
              BRACKET_CLOSE;
          }

    The ``self_send_n`` macro stores the repetition number inside the token
    itself.  When the current token contains a repeated token identifier
    ``TokenID``, then the call to the ``.receive()`` function returns the same
    token ``N`` times repeatedly before starting a new analysis. As long as the
    default token classes are used this is implemented automatically.
    Customized token classes need to prepare some information about how the
    repetition number is to be stored inside the token class (see :ref:`
    _sec-customized-token-class:`).

.. cfunction:: self_send1(TokenID, Str)

    This allows to call the token's ``take_text`` function to set text content
    to what is specified by the zero terminated string ``Str``. ``Str`` must
    be of type 'pointer to ``QUEX_TYPE_LEXATOM``'.

.. warning::

    The token passed to 'self_send1(...)' and the like *must* be of the 
    type ``QUEX_TYPE_LEXATOM`` and *must* have the same coding as 
    the internal buffer. You might want to consider '--bet wchar_t' 
    as buffer size when using converters. Then strings constants like 
    ``L"something"`` could be conveniently passed.

.. cfunction:: self_send2(TokenID, Begin, End)

    This corresponds to a call to the current token's ``take_text`` function
    where ``Begin`` and ``End`` define the boundaries of the string to be
    taken. Both have to be of type 'pointer to ``QUEX_TYPE_LEXATOM``'.

.. warning::

   Relevant for token passing policy *users_token*.  With this token policy no
   tokens can be sent inside incidence handlers.

The actual mechanism of sending consists of three steps:

   #. Fill token content.

   #. Set the current token's identifier.

   #. Increment or set the current token's pointer to the next
      token to be filled.

Depending on the particularities of the setup, the send macros adapt
automatically.  For example, they take care whether the token identifier is
stored in a return value, in a token member variable, or in both. If plain send
functions are not enough the for filling content into the token, the first step
must be implemented by hand, followed by an appropriate send function call. The
function ``self_token_p()`` respectively ``self.token_p()`` gives access to the
current token via pointer.  The pointer to the token may be used to prepare it
*before* sending it out. The three mentioned steps above may, for example, be
implemented like this

.. code-block:: cpp

   self.token_p()->set_number(...);
   self.token_p()->take_text(LexemeBegin + 1, LexemeEnd -2);
   self_send(QUEX_TKN_ID_SPECIAL);

When the token policy 'queue' is used, multiple such sequences can be performed
without returning to the caller of the lexical analyzer.  Modes can be switched
with the ``<<``-operator, as shown in the example, or ``enter_mode``. For
example

.. code-block:: cpp

        {P_STRING_DELIMITER} {
            self.enter_mode(STRING_READER); 
            RETURN;
        }

causes a mode transition to the ``STRING_READER`` mode as soon as a string
delimiter arrives. A mode's id can be mapped to a mode object, and via the two
functions

.. cfunction:: QuexMode&  map_mode_id_to_mode(const int ModeID);

.. cfunction:: QuexMode&  map_mode_to_mode_id(const int ModeID);

The current mode of the lexical analyzer can be queried using the functions

.. cfunction:: QuexMode&           mode();

.. cfunction:: const std::string&  mode_name() const;

.. cfunction:: const int           mode_id() const;

If one wants to avoid the call of exit and enter incidence handlers, then modes can
also set brutally using the member functions:

.. cfunction:: void set_mode_brutally(const int ModeID);

.. cfunction:: void set_mode_brutally(const QuexMode& Mode);

Using these functions only the current mode is adapted, but no incidence handlers
are called. This also means that mode transition control is turned off.
Inadmissible transitions triggered with these functions cannot be detected
during run-time.

In addition to direct mode transitions, modes can be pushed and popped similar to subroutine calls (without arguments). This is provided by the functions:

.. cfunction:: void push_mode(quex_mode& new_mode);

.. cfunction:: void pop_mode();

.. cfunction:: void pop_drop_mode();

The member function push_mode(new_mode) pushes the current mode on a
last-in-first-out stack and sets the new_mode as the current mode. A call to
pop_mode() pops the last mode from the stack and sets it as the current mode.
Note, that the mode transitions with push and pop follow the same mode
transition procedure as for entering a mode directly. This means, that the
on_exit and on_entry handler of the source and target mode are called.

Mode Objects
------------

Modes themselves are implemented as objects of classes which are derived from
the base class quex_mode. Those mode objects have member functions that provide
information about the modes and possible transitions:

.. code-block:: cpp

    bool  has_base(const quex_mode& Mode,       bool PrintErrorMsgF = false) const;
    bool  has_entry_from(const quex_mode& Mode, bool PrintErrorMsgF = false) const;
    bool  has_exit_to(const quex_mode& Mode,    bool PrintErrorMsgF = false) const;
    const int     ID; 
    const string  Name; 

The first three member functions return information about the relation to
other modes. If the flag ``PringErrorMsgF`` is set than the function will print an
error message to the standard error output in case that the condition is not
matched. This comes very handy when using these functions in ``assert``s or during
debugging. The functions can be applied on a given mode object or inside the
``on_entry`` and ``on_exit`` functions with the this pointer. In a pattern action
pair, for example, one might write

.. code-block:: cpp

     if( PROGRAM.has_base(self.mode()) )
         cerr << "mode not a base of PROGRAM: " << self.mode_name() << endl;

For the end-user these functions are not really relevant, since quex itself
introduces ``assert`` calls on mode transitions and provides convienient member
functions in the lexical analyser class to access information about the current
mode.


.. cfunction:: 

.. warning::

   Relevant for token passing policies *users_token*, *users_queue*, and
   *users_mini_queue* when a customized token type is used.

   If you use a customized token type that contains pointers, make sure that
   you read the section about token passing policies :ref:`sec-token-policies`.
   The point is that the ``send()`` functions may override these pointers
   without being referred to elsewhere. It must be ensured that the pointers in 
   received tokens are stored elsewhere, before the analyzer overwrites it.

   

