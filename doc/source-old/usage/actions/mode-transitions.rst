.. _sec-mode-transitions:

Mode Transitions
================

The transition from one mode to another can be controlled via the commands ``GOTO``, 
``GOSUB``, and ``GOUP``. Consider an example of usage of ``GOTO`` for mode transitions:

.. code-block:: cpp

    mode NORMAL {
        "<" => GOTO(TAG);
        .   => QUEX_TKN_LETTER(Lexeme);
        
    }
    mode TAG {
        ">" => GOTO(NORMAL);
        .   => QUEX_TKN_LETTER(Lexeme);
    }

There are two modes ``NORMAL`` and ``TAG``. As soon as an opening ``<`` arrives
the analyzer transits from ``NORMAL`` mode to ``TAG`` mode. As soon as the
closing ``>`` arrives, the analyzer transits back to ``NORMAL`` mode.

Additionally to the mode transition, tokens can be sent if more arguments are
added. The syntax is similar to the brief token senders mentioned in
:ref:`sec:usage-sending-tokens`.  If it is required to send tokens for the tag
regions, the above example may be extended as follows

.. code-block:: cpp

    mode NORMAL {
        "<"  => GOTO(TAG, QUEX_TKN_OPEN_TAG(Lexeme));
        "<<" => GOTO(TAG, QUEX_TKN_OPEN_TAG(text=Lexeme, number=2));
        .    => QUEX_TKN_LETTER(Lexeme);
        
    }

When transitions to and from the ``TAG`` mode are triggered, tokens
with the token-ids ``QUEX_TKN_OPEN_TAG`` and ``QUEX_TKN_CLOSE_TAG`` are also produced.
Additional arguments, such as the ``Lexeme`` can be passed in the same manner as 
when sending normal tokens.

In case that one enters a mode from different other modes, the use of the mode
stack comes handy. Imagine a mode ``FORMAT_STRING`` for parsing ANSI-C-like
format strings. Now, those format strings may occur in a ``PROGRAM`` mode and
in a ``MATH`` mode. If ``GOSUB`` is used instead of ``GOTO`` then the engine
remembers the previous mode. The next ``GOUP`` triggers a transition to this
previous mode. Theoretically, the depth of sub-modes is only restricted by the
computer's memory. Practically, using a depth of more than two risks to 
end up in confusing mode transition behavior. In this cases the use
of mode transition restrictions <<sec mode-options>> becomes a useful tool
in order to detect undesired mode changes.

.. code-block:: cpp

    mode PROGRAM {
        ...
        \"         => GOSUB(FORMAT_STRING,  QUEX_TKN_OPEN_STRING);
        ...
    }

    mode MATH {
        ...
        \"         => GOSUB(FORMAT_STRING, QUEX_TKN_OPEN_STRING);
        ...
    }

    mode FORMAT_STRING {
        ...
        \"         => GOUP(QUEX_TKN_CLOSE_STRING);
        ...
    }

As with ``GOTO`` additional arguments indicate a token sending. Those
arguments are applied on the constructor for the resulting token. Inside
C++ code the mode transitions can be controlled by the member functions
of the analyzer

.. code-block:: cpp

    void    enter_mode(/* NOT const*/ QUEX_NAME(Mode)& TargetMode);
    void    push_mode(QUEX_NAME(Mode)& new_mode);
    void    pop_mode();
    void    pop_drop_mode();

Respectively, in C mode transitions are controlled by

.. code-block:: cpp

    void    QUEX_NAME(enter_mode)(L*, QUEX_NAME(Mode)& TargetMode);
    void    QUEX_NAME(push_mode)(L*, QUEX_NAME(Mode)& new_mode);
    void    QUEX_NAME(pop_mode)(L*, );
    void    QUEX_NAME(pop_drop_mode)(L*, );

where ``L*`` is a pointer to the generated lexical analyzer. Inside 
a lexical analyzer, the following macros work in both environments, C
and C++.

.. code-block:: cpp

    #define self_enter_mode(ModeP)  ...
    #define self_pop_mode()         ...
    #define self_pop_drop_mode()    ...
    #define self_push_mode(ModeP)   ...


.. note::

   When a sub mode is entered the 'return mode' needs to be stored on 
   a stack. This stack has a fixed size. It can be specified via the 
   macro::

       QUEX_SETTING_MODE_STACK_SIZE

   A basis for using the sub mode feature is that there is a clear idea
   about the possible mode transitions. Thus, the number of possible
   'gosubs' should be determined at the time of the design of the lexical 
   analyzer. The default setting is eight.


