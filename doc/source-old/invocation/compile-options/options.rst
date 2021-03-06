Options
-------

For the sake of simplicity only the positive options are mentioned. For each (or most)
of the options below, there exists a sibling with a ``_DISABLED`` suffix. The option without
the suffix enables something, the option with the suffix disables the 'something'.

.. cmacro:: QUEX_OPTION_ASSERTS

   Explicitly enables asserts which are enabled by default anyway. 
   More of use is the sibling ``QUEX_OPTION_ASSERTS_DISABLED``. Disabling
   asserts is key for getting reasonable performance.

.. cmacro:: QUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE

   If defined (as by default) mode changes may happen without a token being
   returned. Then, the analysis process continues until the first valid token is
   returned. However, if::
   
        QUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE_DISABLED

   is defined, then the ``.receive()`` function returns always without 
   checking that a token has actually been sent. This option is only
   effective for the token policy 'single'. With the 'queue' token 
   policy, the analyzer never returns with an empty token queue.

.. cmacro:: QUEX_OPTION_BUFFER_BASED_ANALYZIS

   Turn on buffer based analysis. In particular automatic buffer reload is
   disabled. Also some consistency checks are disabled if asserts were enabled.

.. cmacro:: QUEX_OPTION_COLUMN_NUMBER_COUNTING

   Enables column number counting. Respectively, 
   ``QUEX_OPTION_COLUMN_NUMBER_COUNTING_DISABLED`` 
   disables it.

.. cmacro:: QUEX_OPTION_COMPUTED_GOTOS

   Enables/disables the usage of computed gotos. Use this option only if your
   compiler supports it. For example, GNU's gcc does support it from version 2.3.

.. cmacro:: QUEX_OPTION_CONVERTER_ICONV

   Enables/disables the use of the GNU IConv library for conversion. This can also be set with the command line option ``--iconv``.

.. cmacro:: QUEX_OPTION_CONVERTER_ICU

   Enables/disables the use of the IBM's ICU library for conversion. This can also be
   set with the command line option ``--icu``. Note, that IConv and ICU are
   best used mutually exclusive.

.. cmacro:: QUEX_OPTION_DEBUG_SHOW

   Enables/disables the output of details about the lexical analysis process.

.. cmacro:: QUEX_OPTION_DEBUG_SHOW_LOADS

   Enables/disables the output of details about reloads of the buffer.

.. cmacro:: QUEX_OPTION_ENABLE_PINARD_RECODE

   Enables/disables Francois Pinards Recode library. At the time of this writing the 
   converter is not yet implemented.

.. cmacro:: QUEX_OPTION_ERROR_OUTPUT_ON_MODE_CHANGE_ERROR

   Enables/disables error messages on disallows mode transitions.

.. cmacro:: QUEX_OPTION_INCLUDE_STACK

   Enables/disables the feature of an intelligent include stack. 

.. cmacro:: QUEX_OPTION_INFORMATIVE_BUFFER_OVERFLOW_MESSAGE

   Enables/disables informative buffer overflow messages. If set it prints the lexeme
   on which the buffer overflow happened.

.. cmacro:: QUEX_OPTION_LINE_NUMBER_COUNTING

   Enables/disables line number counting. Line and column number counting
   are implemented very efficiently. Most probably no performance decrease
   will be measurable by deactivating this feature.

.. cmacro:: QUEX_OPTION_POST_CATEGORIZER

   Enables/disables an optional 'post categorizer' that maps from a lexeme to a token-id.

.. cmacro:: QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK

   Enables/disables mode transition checks during run-time.

.. cmacro:: QUEX_OPTION_STRANGE_ISTREAM_IMPLEMENTATION

   Some input streams behave rather strange. When receiving ``N`` characters
   from a stream, their stream position might increase by a number ``M`` which
   is different from ``N``. To handle those streams, set this option. 

   Alternatively, one might consider opening the stream in binary mode.

.. cmacro:: QUEX_OPTION_TERMINATION_ZERO_DISABLED

   If this macro is defined, the setting of the terminating zero at the end of
   a lexeme is disabled. This may cause some speed-up, but it is necessary
   in order to run the lexical analyzer on read-only memory.

.. cmacro:: QUEX_OPTION_STRING_ACCUMULATOR

   Enables/disables an optional accumulator which can collect some longer string.

.. cmacro:: QUEX_OPTION_TOKEN_POLICY_QUEUE

   Enables/disables the token sending via a token queue. With the current version of quex (0.36.4)
   some performance increase can be achieved if the token queue is disabled.

.. cmacro:: QUEX_OPTION_TOKEN_POLICY_SINGLE

   Enables/disables the token sending via a token object owned by the user. 

.. cmacro:: QUEX_OPTION_TOKEN_STAMPING_WITH_LINE_AND_COLUMN

   Enables/disables the stamping of tokens with the line and column number.
   The stamping happens by default. If it is desired to disable this stamping
   the ``..._DISABLED`` version of this macro must be defined. If column or
   line counting is disabled the corresponding stamping is also disabled,
   anyway.

.. cmacro:: QUEX_OPTION_WARNING_ON_PLAIN_FILLER_DISABLED

   Disable the warning message that is printed if a analyzer is used without
   a character encoding while it was created for a converter interface such
   as IConv or ICU.

.. cmacro:: QUEX_OPTION_SEND_AFTER_TERMINATION_ADMISSIBLE 

   If asserts are enabled, then quex triggers an error message whenever
   a token is sent after the 'TERMINATION' token. In some cases, this 
   might just be convenient, so that one might want to allow it by
   defining this macro.

