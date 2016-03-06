Types
-----

.. cmacro:: QUEX_TYPE_ANALYZER_FUNCTION

   Function pointer type of the analyzer function. Best not to be changed.

.. cmacro:: QUEX_TYPE_LEXATOM

   Internal carrier type for characters. This is set automatically by quex
   if the command line option ``-b`` or ``--buffer-element-size`` is specified.

.. cmacro:: QUEX_TYPE_TOKEN_ID

   Type to be used to store the numeric value of a token identifier. On small systems
   this might be set to ``short`` or ``unsigned char``. On larger systems, if very
   many different token-ids exits (e.g. > 2e32) then it might be set to ``long``.
   It might be more appropriate to use standard types from ``stdint.h``
   such as ``uint8_t``, ``uint16_t`` etc.

   The character type can also be specified via the command line option ``-b``, 
   or ``--buffer-element-size``.

