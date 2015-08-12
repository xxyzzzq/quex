Struct
===============================================================================

This directory contains files concerned with construction, destruction,
file-inclusion, and reset. All of these deal with the setup of a lexical
analyzer object. The API for the related operations was designed to follow
a homogeneous scheme. It should allow easy handling for the standard
case. The level of required detail knowledge increases with the deviation
from what is considered the most expected use case. 

A lexical analyzer runs on a content presented in a chunk of memory. This
way it can be accessed quickly. If the engine's codec differs from the codec
of the input stream it must be converted. The general concept of buffer
filling performs this task. Depending on the platform, files or streams
are accessed in different manners. To cope with different operating systems
and platforms, the byte loading is abstracted through a byte loader class.


   file, stream,      .------------.      .--------------.     .--------.
   message, or   <--->| ByteLoader |<---->| BufferFiller |---->| Buffer |
   signal, etc.       '------------'      '--------------'     '--------'
                        <File API>          <Conversion>       <Analysis>

The lexical analyzer's engine is generated and its output is determined by the
user defined reaction to matching patterns. What remains to be discussed is the
control over the input. In the most expected case a user would parse a file.
Thus, there should be a way to construct a lexical analyzer from a file name.
Additionally, a conversion codec may be specified which defines a character
conversion before parsing. Internally, the most expected file handle type
``FILE`` is used to access the file with the given name. The abstracted loader
interface is therefore ``ByteLoader_FILE`` nesting the opened file handle. 
Together with the conversion codec's name a ``BufferFiller_Conversion``
or a ``BufferFiller_Plain`` can be constructed. This object is then used
to fill the buffer. 

                       
                  .-------------------. (1)
   input name --->| handle associated |
   handle type -->| with input        |
                  '-------------------'
                          | input handle
                          |
                  .-----------------.   (2)
                  |   Byte loader   |
                  |   object        |
                  '-----------------'
                          | byte loader
                          |
                  .-----------------.   (3)
    conversion -->|  Buffer Filler  |                 memory
    codec         '-----------------'              specification
                          |                             |
                          |                             |
                  .------------------.  (5)   .---------------------. (6)
                  | filling approach |        |  pointing approach  |
                  '------------------'        '---------------------'
                          |                             |
                          '-----------.   .-------------'
                                    remaining           
                                   construction


The constructor in C++ for level '1' is 

            X(FileName, CodecName);

If a specific input handle is to be used, for which a byte loader already exists
it may be used and the construction process may be entered at level '2'. The
constructors for that are

           X(FILE*, CodecName);               // Standard C Library
           X(int, CodecName);                 // POSIX File Handles
           X(std::istream*, CodecName);       // Standard C++ Library
           X(std::wistream*, CodecName);      // Standard C++ Library   

In case, there is no byte loader class that fits the user's environment,
byte loader may be derived from 'ByteLoader'. An object of this type
may then be passed to the constructor of level '3'.

           X(ByteLoader*, CodecName);

Depending on the conversion codec name, a BufferFiller object is constructed.
If the CodecName = 0, no conversion is applied and the BufferFiller_Plain
is used. Else, the default conversion library is used to construct a 
BufferFiller_Converter. If a dedicated BufferFiller is required, for example,
if the raw buffer size needs to be manually configured, then the constructor
for level '4' needs to be called with an object derived from BufferFiller.

           X(BufferFiller*);

The ownership of the objects passed to the constructors is passed to the
created objects! That means, the the user is not responsible for freeing
the associated memory.

Quex allows also analyzers running on memory where the user points to. 
In that case, it is assumed that the user takes care of all filling. The
BufferFiller remains a pointer to ``NULL``. The constructor to be used
is 

           X(QUEX_TYPE_CHARACTER* BufferMemoryBegin, 
             size_t               BufferMemorySize,
             QUEX_TYPE_CHARACTER* BufferEndOfFileP); 

