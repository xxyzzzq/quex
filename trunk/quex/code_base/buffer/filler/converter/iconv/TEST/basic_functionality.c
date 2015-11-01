#include <basic_functionality.h>
#include <hwut_unit.h>
#define REFERENCE_DIR    "../../../../TESTS/navigation/TEST/examples/"
#define ARRAY_ELEMENT_N  65536

QUEX_NAMESPACE_MAIN_OPEN

static void         prepare(const char* CodecName);
static const char*  get_input_file_name(const char* Codec);
static const char*  find_reference(const char* file_stem);
static size_t       load(const char* FileName, void* buffer, size_t Size);
static void         verify_completion(QUEX_NAME(Converter)* converter, 
                                      uint8_t* source_p, QUEX_TYPE_CHARACTER* drain_p);
static void         verify_source_content(uint8_t*       SourceP, 
                                          const uint8_t* SourceEndP);
static void         verify_drain_content(QUEX_TYPE_CHARACTER*       Drain, 
                                         const QUEX_TYPE_CHARACTER* DrainEndP);
static void         verify_call_to_convert(QUEX_NAME(Converter)*      converter,
                                           uint8_t**                  source_pp, 
                                           const uint8_t*             SourceEndP,
                                           QUEX_TYPE_CHARACTER**      drain_pp,  
                                           const QUEX_TYPE_CHARACTER* DrainEndP,
                                           bool                       DrainFilledF);
static void         poison_drain_buffer();

uint8_t             source[ARRAY_ELEMENT_N];
uint8_t             source_backup[ARRAY_ELEMENT_N];
int                 source_byte_n;
QUEX_TYPE_CHARACTER drain[ARRAY_ELEMENT_N];
QUEX_TYPE_CHARACTER drain_nominal[ARRAY_ELEMENT_N];
int                 drain_character_n;

void
test_conversion_in_one_beat(QUEX_NAME(Converter)* converter, const char* CodecName)
{
    uint8_t*              s_p;
    QUEX_TYPE_CHARACTER*  d_p;
    int                   i;

    prepare(CodecName);

    for(i = 0; i < 3; ++i) {
        poison_drain_buffer();

        s_p = &source[0];
        d_p = &drain[0];

        /* Complete source is present => conversion must be complete.
         * converter must return 'true.'                                     */
        verify_call_to_convert(converter, &s_p, &source[source_byte_n],
                               &d_p, &drain[drain_character_n], 
                               /* FilledF */ true);

        verify_completion(converter, s_p, d_p);
    }
}

void
test_conversion_stepwise_source(QUEX_NAME(Converter)* converter, 
                                const char*           CodecName)
{
    uint8_t*              s_p;
    QUEX_TYPE_CHARACTER*  d_p;
    int                   i;

    prepare(CodecName);

    for(i = 0; i < 3; ++i) {
        poison_drain_buffer();

        s_p = &source[0];
        d_p = &drain[0];
        for(i = 0; i < source_byte_n; ++i) {
            /* As long as the last source byte has not been received, the drain
             * can never be full.                                            */
            verify_call_to_convert(converter, &s_p, &source[i+1], 
                                   &d_p, &drain[drain_character_n], 
                                   (i == source_byte_n) ? true : false);
        }
        verify_completion(converter, s_p, d_p);
    }
}

void
test_conversion_stepwise_drain(QUEX_NAME(Converter)* converter, 
                               const char*           CodecName)
{
    uint8_t*              s_p;
    QUEX_TYPE_CHARACTER*  d_p;
    int                   i;

    prepare(CodecName);

    for(i = 0; i < 3; ++i) {
        poison_drain_buffer();

        s_p = &source[0];
        d_p = &drain[0];
        for(i = 0; i < drain_character_n; ++i) {
            /* There are always enough source bytes to fill the drain character
             * as long as i < drain_character_n.                             */
            verify_call_to_convert(converter, &s_p, &source[source_byte_n], 
                                   &d_p, &drain[i+1], /* FilledF */ true);
        }
        
        verify_completion(converter, s_p, d_p);
    }
}

static void
prepare(const char* CodecName)
{
    const char*  file_name           = get_input_file_name(CodecName);
    const char*  reference_file_name = find_reference(file_name);

    /* Poison all buffers, so that bad steps cause failure. */
    memset(&source[0], 0xFF, sizeof(source));
    memset(&source_backup[0], 0xFF, sizeof(source_backup));
    memset(&drain[0], 0xFF, sizeof(drain));
    memset(&drain_nominal[0], 0xFF, sizeof(drain_nominal));

    /* Load content into source and nominal drain. */
    source_byte_n     = load(file_name, &source[0], ARRAY_ELEMENT_N);
    drain_character_n = load(reference_file_name, &drain_nominal[0], 
                           ARRAY_ELEMENT_N * sizeof(QUEX_TYPE_CHARACTER))
                      / sizeof(QUEX_TYPE_CHARACTER);
    hwut_verify(source_byte_n);
    hwut_verify(drain_character_n);

    /* Backup the source, so it s checked that source is not altered. */
    memcpy(&source_backup[0], &source[0], source_byte_n);
}

const char* 
get_input_file_name(const char* Codec)
{
    if     ( strcmp(Codec, "ASCII") == 0 ) return REFERENCE_DIR "festgemauert";
    else if( strcmp(Codec, "UTF8") == 0 )  return REFERENCE_DIR "languages";
    else if( strcmp(Codec, "UTF16") == 0 ) return REFERENCE_DIR "small";
    else                                   return "";
}

static const char*
find_reference(const char* file_stem)
/* Finds the correspondent unicode file to fill the reference buffer with
 * pre-converted data. A file stem 'name' is converted into a file name 
 *
 *             name-SIZE-ENDIAN.dat
 *
 * where SIZE indicates the size of a buffer element in bits (8=Byte, 16= 
 * 2Byte, etc.); ENDIAN indicates the system's endianess, 'le' for little
 * endian and 'be' for big endian. 
 */
{
    static char file_name[256];

    if( sizeof(QUEX_TYPE_CHARACTER) == 1 ) {
        snprintf(&file_name[0], 255, "%s.dat", file_stem);
    }
    else {
        snprintf(&file_name[0], 255, "%s-%i-%s.dat", file_stem, sizeof(QUEX_TYPE_CHARACTER)*8, 
                 QUEXED(system_is_little_endian)() ? "le" : "be");
    }
    return &file_name[0];
}

static size_t      
load(const char* FileName, void* buffer, size_t Size)
{
    FILE*      fh;
    size_t     loaded_byte_n;

    fh = fopen(FileName, "rb");
   
    if( !fh ) {
        printf("Could not load '%s'.\n", FileName);
        return 0;
    }

    loaded_byte_n = fread(buffer, 1, Size, fh);
    fclose(fh);
    return loaded_byte_n;
}

static void
verify_completion(QUEX_NAME(Converter)* converter, 
                  uint8_t* source_p, QUEX_TYPE_CHARACTER* drain_p)
{
    /* Nothing shall be left in stomach. */
    hwut_verify(converter->stomach_byte_n(converter) == 0);
    hwut_verify(source_p - &source[0] == source_byte_n);

    /* All is converted. */
    hwut_verify(drain_p - &drain[0] == drain_character_n);

    /* Converted content must be correct! */
    verify_drain_content(&drain[0], &drain[drain_character_n]);

    /* Input buffer is NOT to be touched. */
    verify_source_content(&source[0], &source[source_byte_n]);

    /* '.stomach_clear()' shall not do any harm. */
    converter->stomach_clear(converter);
}


static void
poison_drain_buffer()
{
    memset(&drain[0], 0x5A, drain_character_n * sizeof(QUEX_TYPE_CHARACTER));
}

static void
verify_call_to_convert(QUEX_NAME(Converter)* converter,
                       uint8_t**             source_pp, const uint8_t*             SourceEndP,
                       QUEX_TYPE_CHARACTER** drain_pp,  const QUEX_TYPE_CHARACTER* DrainEndP,
                       bool                  DrainFilledF)
{
    uint8_t* s_p_before = *source_pp;
    uint8_t* d_p_before = *drain_pp;
    bool     filled_f;

    filled_f = converter->convert(converter, source_pp, SourceEndP, 
                                  drain_pp, DrainEndP); 

    hwut_verify(filled_f == DrainFilledF);

    hwut_verify(s_p_before <= *source_pp && *source_pp <= SourceEndP);
    hwut_verify(d_p_before <= *drain_pp  && *drain_pp  <= DrainEndP); 
    hwut_verify(*source_pp + converter->stomach_byte_n(converter) < SourceEndP);

    /* Converted content must be correct! */
    verify_drain_content(d_p_before, *drain_pp);

    /* Input buffer is NOT to be touched. */
    verify_source_content(s_p_before, *source_pp);
}

static void
verify_source_content(uint8_t* SourceP, const uint8_t* SourceEndP)
{
    const ptrdiff_t Offset = SourceP - &source[0];
    const size_t    Size   = (size_t)(SourceEndP - SourceP);

    hwut_verify( 
        memcmp((void*)&source_backup[Offset], (void*)SourceP, Size) == 0
    );
}

static void
verify_drain_content(QUEX_TYPE_CHARACTER* DrainP, const QUEX_TYPE_CHARACTER* DrainEndP)
{
    const ptrdiff_t   Offset = DrainP - &drain[0];
    const size_t      Size   = (size_t)(DrainEndP - DrainP);

    hwut_verify( 
        memcmp((void*)&drain_nominal[Offset], (void*)DrainP, Size) == 0
    );
}

QUEX_NAMESPACE_MAIN_CLOSE
