.. _sec-customized-converters:

Customized Converters
=====================

For 'normal' applications the provided converters provide enough performance
and a sufficiently low memory footprint. There is no need for the user to
implement special converters. However, it might become interesting when it
comes to tuning.  If someone knows that the UTF-8 encoding mostly reads
characters from a specific code page it is possible to provide an optimized
converter that is able to speed up a bit the total time for lexical analysis.
Also, by means of this feature it is possible to scan personalized encodings. 

Converters can be added to the quex engine very much in a plug-and-play manner.
Nevertheless, this section is considered to be read by advanced users. Also,
the effort required for implementing and testing a dedicated converter might
exceed the time budgets of many projects. Lexical analyzers can be generated
with quex, literally, in minutes. Implementing personalized converters together
with the implementation of unit tests, however, can easily take up a whole week. 

For everyone who is not yet scared off, here comes the explanation: A converter
for a buffer filler is an object that contains the following function pointers
described here in a simplified manner, without precise type definitions:

.. code-block:: cpp

   struct QuexConverter {

        void    (*open)(struct QuexConverter*, 
                        const char* FromCodingName, 
                        const char* ToCodingName);  

        bool    (*convert)(struct QuexConverter*, 
                           uint8_t**                  source, 
                           const uint8_t*             SourceEnd, 
                           QUEX_TYPE_LEXATOM**      drain,  
                           const QUEX_TYPE_LEXATOM* DrainEnd);

        /* optional: can be set to 0x0 */
        void    (*on_conversion_discontinuity)(struct QuexConverter*);  

        void    (*delete_self)(struct QuexConverter*);  

        bool    dynamic_character_size_f;
   };

Each function points to an implementation of a function that interacts the the library
or the algorithm for character conversion. The role of each function is explained in the following list.

.. cfunction:: open(...)

        This opens internally a conversion handle for the conversion from 'FromCodingName'
        to ``ToCodingName``. Pass ``0x0`` as ``ToCodingName`` in order to indicate a conversion
        to Unicode of size sizeof(QUEX_TYPE_LEXATOM). 
                
        It is the task of the particular implementation to provide the 'to coding'
        which is appropriate for sizeof(QUEX_TYPE_LEXATOM), i.e. ASCII, UCS2, UCS4.

        Based on the ``FromCodingName`` this function needs to decide whether the
        character encoding is fixed size or dynamic size. According to this, the
        flag ``dynamic_character_size_f`` needs to be set. Setting it to ``true``
        is safe, but may slow down the stream navigation.
        
        
.. cfunction:: convert(...)

        Function ``convert`` tries to convert all characters given in ``source`` with the
        coding specified earlier to _open(...). ``source`` and ``drain`` are passed as
        pointers to pointers so that the pointers can be changed. This way the
        converter can inform the user about the state of conversion from source to
        drain buffer.::
                
                   START:
                                *source              SourceEnd
                                |                    |
                         [      .....................]   source buffer
                
                              *drain         DrainEnd
                              |              |
                         [....               ] drain buffer
                
        At the beginning, 'source' points to the first character to be
        converted. 'drain' points to the place where the first converted
        character is to be written to.::
                 
                   END:
                                                *source                              
                                                |     
                         [                      .....]   source buffer
                
                                       *drain 
                                       |      
                         [.............      ] drain buffer
                
        After convertsion, ``source`` points immediately behind the last 
        character that was subject to conversion. ``drain`` points behind the
        last character that resulted from the conversion. 

        This function must provide the following return values
                 
        .. data:: true    
           
           Drain buffer is filled as much as possible with converted characters.

        .. data:: false    

           More source bytes are needed to fill the drain buffer.     

.. cfunction:: on_conversion_discontinuity(...)    

        The function ``on_conversion_discontinuity`` is called whenever a conversion discontinuity appears.
        Such cases appear only when the user navigates through the input
        stream (seek_character_index(...)), or with long preconditions when
        the buffer size is exceeded. 
            
        For 'normal' converters this function can be set to '0x0'. If a converter
        has an internal 'stateful-ness' that is difficult to be tamed, then use
        this function to reset the converter. Actually, the initial reason
        for introducing the function pointer was the strange behavior of the 
        ICU Converters of IBM(R). Note, that if the function pointer is set, then
        the buffer filler does not use any hints on character index positions. This
        may slow down the seek procedure. If a precondition makes it necessary to load
        backwards, or the user navigates arbitrarily in the buffer stream there
        can be significant trade-offs.

.. cfunction:: delete_self(...)    

        This function closes the conversion handle produced with open(...) and      
        deletes the object of the conversion object, in the same way as a virtual
        constructor does.

.. cvar:: bool dynamic_character_size_f

        This flag needs to be set to allow the buffer filler to allow its algorithms
        for character stream navigation.

For all functions mentioned above the user needs to implement to which those
function pointer can point.  In the next step, a user defined converter must be
derived from ``QuexConverter``. This should happen in the C-way-of-doing-it.
That means, that ``QuexConverter`` becomes the first member of the derived
class[f#1]_ . Consider the implementation for GNU IConv as an example

.. code-block:: cpp

    typedef struct {
        QuexConverter  base;

        iconv_t        handle;

    } QuexConverter_IConv;

As another example consider the implementation of a converter class for IBM's ICU:

.. code-block:: cpp

    typedef struct {
        QuexConverter  base;

        UConverter*  from_handle;
        UConverter*  to_handle;
        UErrorCode   status;

        UChar        pivot_buffer[QUEX_SETTING_ICU_PIVOT_BUFFER_SIZE];
        UChar*       pivot_iterator_begin;
        UChar*       pivot_iterator_end;

    } QuexConverter_ICU;

The role of the derived class (``struct``) is to contain data which is
important for the conversion process.  As an example, let the user defined
converter functions be defined as 

.. code-block:: cpp

    void
    CryptoConverter_open(CryptoConverter*  me, 
                         const char* FromCodingName, 
                         const char* ToCodingName);

    bool
    CryptoConverter_convert(CryptoConverter*  me
                            uint8_t**       source, 
                            const uint8_t*  SourceEnd, 
                            QUEX_TYPE_LEXATOM**       drain,  
                            const QUEX_TYPE_LEXATOM*  DrainEnd);
    void 
    CryptoConverter_on_conversion_discontinuity(CryptoConverter*  me);

    void
    CryptoConverter_delete_self(CryptoConverter*  me);

Note, that the function signatures contain a pointer to ``CryptoConverter`` as
a ``me`` pointer [#f2]_, where the required function pointers require a pointer to
a ``QuexConverter`` converter object. This is no contradiction. When the buffer filler
creates an object of the derived type ``CryptoConverter`` is stores the pointer to
it in as pointer to ``QuexConverter``. The member functions, though, know that
they work on an object of the derived class ``CryptoConverter``. 

Once, the access functions and the dedicated class have been defined a function
needs to be implemented that creates the converter. This needs to following:

#. Allocate space for the converter object. The allocation method for the converter
   object must correspond the deletion method in ``delete_self``. A simple
   way to implement this is to rely on ``malloc`` like this

   .. code-block:: cpp

      ...
      me = (CryptoConverter*)malloc(sizeof(CryptoConverter));
      ...

   provided that the ``delete_self`` function is implemented like

   .. code-block:: cpp

        void
        CryptoConverter_delete_self(CryptoConverter*  me) {
            /* de-initialize resources */
            ...
            free(me);   /* corresponding call to 'malloc' */
        }

   Note, that quex provides you with sophisticated methods of memory management <<>>.
   This is the point where you can plug-in the memory allocation method for 
   your converter object.

#. Set the function pointers for ``open``, ``convert``, 
   ``on_conversion_discontinuity``, and ``delete_self``. The assignment
   of function pointers require a type cast, because the first argument
   differs. In the example above, the assignment of function pointers
   is

   .. code-block:: cpp

        ...
        /* assume that 'me' has been allocated */
        me->base.open        = (QUEX_NAME(QuexConverterFunctionP_open))CryptoConverter_open;
        me->base.convert     = (QUEX_NAME(QuexConverterFunctionP_convert))CryptoConverter_convert;
        me->base.delete_self = (QUEX_NAME(QuexConverterFunctionP_delete_self))CryptoConverter_delete_self;
        me->base.on_conversion_discontinuity = \
           (QUEX_NAME(QuexConverterFunctionP_on_conversion_discontinuity))\
           CryptoConverter_on_conversion_discontinuity;
        ...

   The macro ``QUEX_NAME(...)`` is used to identify the namespace, in case that the lexical
   analyzer is generated for 'C', where there are no namespaces--at the time of this writing.


#. Initialize the converter object. This is not the place to setup or
   allocate any conversion handle. The setup of conversion handles is the
   task of the ``open`` function. The iconv library, for example does not
   more than 
   
   .. code-block:: cpp

        ...
        me->handle = (iconv_t)-1;
        ...

   which assigns something useless to the conversion handle. This way it can be
   easily detected whether the ``open`` call was done properly.

#. Return a pointer to the created object. That is the easiest part:

   .. code-block:: cpp

      ...
      return me;

Now, the only thing that remains is to tell quex about the user's artwork.
Using the command line option ``--converter-new`` (respectively ``--cn``) the
name of the converter creating function can be passed. If, for example, the
this function is named ``CryptoConverter_new``, then the call to quex needs to look
like

.. code-block:: bash

   > quex ... --converter-new CryptoConverter_new ...

Additionally, the compiler needs to know where to find the definition of you
converter class, so you need to mention it in a ``header`` section.

.. code-block:: cpp

   header { 
       ...
       #include "CryptoConverter.h"
       ...
   }

The linker, also, has his rights and needs to be informed about the files of
your converter and the files that implement the converter interface 
(e.g.  ``CryptoConverter.o``). This is all that is required to setup a user 
defined character converter.

.. rubric:: Footnotes

.. [#f1] This ensures that the ``QuexConverter`` object is located in memory at the 
         beginning of the derived class' object. A pointer to the (beginning) of 
         the derived class' object points at the same time to the beginning of the
         member ``base`` which is of type ``QuexConverter``. A pointer to the
         derived class can act seamlessly as a pointer to the base class.

.. [#f2] A ``me`` pointer in C corresponds to the ``this`` pointer in C++. It gives
         access to the objects content.
 
