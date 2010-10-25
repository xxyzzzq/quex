#ifndef ParserBase_ncc_h_included
#define ParserBase_ncc_h_included

namespace scope1
{

class scope2
{
public:
	class scope3
	{
	public:
    	// Symbolic tokens:
	    enum Tokens__
    	{
	        TKN_VAR = 257,
    	    TKN_SEMICOLON,
        	TKN_OP_EQUAL,
	        TKN_OP_PLUS,
    	    TKN_INT,
        	TKN_TYPE_INT,
	        TKN_LPAREN,
    	    TKN_RPAREN,
        	TKN_PRINT,
	        TKN_TERMINATION,
    	    TKN_UNINITIALIZED,
	    };

	}; // scope3::

}; // scope2::

} // scope1::

#endif

