.. _sec-engine-encoding:

Analyzer Engine Codec
=====================

Adapting the internal encoding of the generated lexical analyzer engine happens by
means of the command line flag ``--encoding``. When a encoding is specified the
internal engine will no longer run on Unicode, but rather on the specified
encoding. Consider the example of a lexical analyzer definition for some Greek
text to be encoded in ISO-8859-7:

.. code-block:: cpp

    define {
        CAPITAL   [ΆΈΉΊΌΎ-Ϋ]   // Greek capital letters
        LOWERCASE [ά-ώ]        // Greek lowercase letters
        NUMBER    [0-9][0-9.,]+
    }

    mode X :
    <skip: [ \t\n]>
    {
        {CAPITAL}{LOWERCASE}+  => QUEX_TKN_WORD(Lexeme);
        {NUMBER}               => QUEX_TKN_NUMBER(Lexeme);
        km2|"%"|{LOWERCASE}+   => QUEX_TKN_UNIT(Lexeme);
    }

The resulting state machine in Unicode is shown in 
Figure :ref:`Unicode Engine <fig-encoding-unicode>`. This engine could 
either fed by converted file content using a converting buffer filler. 
Alternatively, it can be converted so that it directly parses ISO8859-7
encoded characters. Specifying on the command line::

   > quex (...) --encoding iso8859_7 (...)

does the job. Note, that no character encoding name needs to be passed
to the constructor, because the generated engine itself inhibits the encoding.
The character encoding name must be specified as '0x0' (if it is to be specified anyway).

.. code-block:: cpp

   quex::MyLexer    qlex(&my_stream);  // character encoding name = 0x0, by default

.. _fig-encoding-unicode:

.. figure:: ../figures/state-machine-encoding-unicode.*
   
   Sample lexical analyzer with an internal engine encoding 'Unicode'.

The result is a converted state machine as shown in figure
:ref:`ISO8859-7 Eninge <fig-encoding-iso8859-7>`. The state machine
basically remains the same, only the transition rules have been adapted.

.. _fig-encoding-iso8859-7:

.. figure:: ../figures/state-machine-encoding-iso8859-7.*

   Sample lexical analyzer with an internal engine encoding 'ISO8859-7' (Greek).

It is worth mentioning that the command line arguments ``--encoding-info`` providing
information about the list of encodings and ``--encoding-for-language`` are useful
for making decisions about what encoding to choose. Note, that in case that the engine
is implemented for a specific encoding, there is no 'coding name' to be passed to
the constructor.

.. note::

   When ``--encoding`` is used, then the command line flag
   ``--buffer-element-size`` (respectively ``-b``), it does not stand for
   the character's width. When quex generates an engine that actually
   understands the encoding, this flag specifies the size of the code elements. 
   
   For example, UTF8 covers the complete UCS code plane. So, its code points
   would require at least three bytes (0x0 - 0x10FFFF). However, the code elements
   of UTF8 are *bytes* and the internal engine triggers on bytes. Thus for encoding ``utf8``
   ``-b 1`` must be specified. In the same way, UTF16 covers the whole plain, but its
   elements consist of *two bytes*, thus here ``-b 2`` must be specified.



The UTF8 Codec
##############

The UTF8 Codec is different from all previously mentioned encodings in the sense that
it encodes Unicode characters in byte sequences of differing lengths. That means that
the translation of a lexical analyzer to this encoding cannot rely on an adaption of
transition maps, but instead, must reconstruct a new state machine that triggers
on the byte sequences. 

Figure :ref:`UTF8 State Machine <fig-utf8-encoding-state-machine>` shows the state
machine that results from a utf8 state split transformation of the state
machine displayed in figure :ref:`fig-encoding-unicode`.  While the encoding
adaptations happen on transition level, the main structure of the state machine
remains in place.  Now however, the state machine undergoes a complete
metamorphosis.


.. _fig-utf8-encoding-state-machine:

.. figure:: ../figures/utf8-encoding-state-machine.*
   
   Sample lexical analyzer with an internal engine encoding 'UTF8'.

.. note:: 

   The skipper tag ``<skip: ...>`` cannot be used cautiously with the utf8 encoding.
   Only those ranges can be skipped that lie underneath the Unicode value 0x7F. This is so
   since any higher value requires a multi-value sequence and the skipper is 
   optimized for single trigger values. 
   
   Skipping traditional whitespace, i.e. ``[ \t\n]`` is still no problem. Skipping 
   Unicode whitespace ``[:\P{White_Space}:]`` is a problem since the Unicode
   property is carried by characters beyond 0x7F.  In general, ranges above 0x7F
   need to be skipped by means of the 'null pattern action pair'.::

   .. code-block:: cpp

        ...
        {MyIgnoredRange}   { }
        ...

The UTF16 Codec
###############

Similar to the UTF8 encoding some elements of the Unicode set of code points are
encoded by two, others by four byte. To handle this type of encoding, quex
transforms the Unicode state machine into a state machine that runs on triggers
of a maximum range of 65536.  The same notes and remarks made about UTF8 remain
valid. However, they are less critical since only those code points are split
into 4 bytes which are beyond 0xFFFF.

There is one important point about UTF16 which is not to be neglected: Byte
Order, i.e. little endian or big endian. In order to work properly the
analyzer engine requires the buffer to be filled in the byte order which is
understood by the CPU. UTF16 has three variants: 

* UTF16-BE for big-endian encoded UTF16 streams.

* UTF16-LE for little endian encoded UTF16 streams.

* UTF16 which does not specify the byte order. Instead, a so called 'Byte Order
  Mark' (BOM) must be prepended to the stream. It consists of two bytes indicating
  the byte order:
 
  - ``0xFE 0xFF`` precedes a big endian stream, and
  - ``0xFF 0xFE`` precedes a little endian stream.

The analyzer generated by quex does not know about byte orders. It only knows
the encoding ``utf16``. The provided stream needs to be provided in the byte
order appropriate for particular CPU. This may mean that the byte order needs to
be reversed during loading. Such a reversion can either passing the information
to the constructor.

.. code-block:: cpp

   quex::MyLexer   qlex(fh, 0x0, /* ReverseByteOrderF */True);

Such a usage is appropriate if the encoding is contrary to the machine's encoding. If, for example
one tries to analyze a UTF16-BE (big endian stream) on an intel pentium (tm) machine, which
is little endian, then the reverse byte order flag can be passed to the constructor. If a
UTF16 stream is expected which specifies the byte order via a byte order mark (BOM), then 
the first bytes are to be read *before* constructor is called, or before a new stream 
is passed to the analyzer. In any case, the byte order reversion can be observed and adapted 
with the following member functions. 

.. code-block:: cpp

   bool     byte_order_reversion();
   void     byte_order_reversion_set(bool Value);

An engine created for encoding ``utf16`` can be used for both, little endian and big endian
data streams. The aforementioned flags allow to synchronize the byte order of the CPU
with the data streams byte order by means of reversion, if necessary.

.. note::

    In the Unicode Standard the code points from 0xD800 to 0xDFFF cannot be
    assigned to any characters. In general, Quex is forgiving if regular
    expressions do not exclude them.  However, when a UTF16-based engine is
    specified, then Quex deletes these code points automatically from any
    pattern. This is necessary, because UTF16 requires this numeric range for
    lead and trail surrogates. 
    
    Since the mentioned code points are not assigned to characters
    text-oriented applications should not recognize a difference. However, for
    non-textual applications, such as DNA-analysis or pattern recognition, this
    might become an issue. In such cases, the range cutting must be taken into
    consideration, or UTF16 is better not used as encoding.

Summary
#######

The command line flag ``--encoding`` allows to specify the internal coding of the
generated lexical analyzer. This enables lexical analyzers that run fast on
encodings different from Unicode or ASCII. However, there are two drawbacks. First
of all not all possible encodings are supported[#f1]_. Second, once an engine has
been created for a particular encoding, the encoding is fixed and the engine can only
run on this encoding. Thus subsequent sections focus on the 'converter approach'
where the internal engine remains running on Unicode, but the buffer filler
performs the conversion. It is not run time efficient as the internal engine
encoding, but more flexible, in case that the generated analyzer has to deal with
a wide range of encodings.

.. warning:: 

    At the time of this writing, the line and column counting for encoding-based
    engines may not work properly for patterns where the length can only be
    determined at run-time. This is due to the fact that not all characters are
    necessarily represented by the same number of bytes and the dynamic line
    and column counter does not reflect on the level of interpreted bytes.
    That means, that it does not know about UTF8, UTF16, etc. Future versions
    may very well incorporate an advanced line and column counter for
    encoding-engines.

    With this respect, it is advantageous to use a converter with a Unicode
    based buffer, rather than the more compact and possibly faster encoding
    based approach.

