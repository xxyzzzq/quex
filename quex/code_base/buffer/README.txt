HOW TO USE THE buffer CLASS:

IMPORTANT: You cannot make two moves forward or backward without
           checking if the result is a border character!

IDEA: This might be optimized, but the code size to implement this
      would probably grow so drastically, that the program would 
      finally run slower.

(*) getting a character in forward direction

	const int tmp = x.get_forward();
	//
	// NOTE: In during 'real' analysis tmp == BOFC should never occur. This case can
	//       only occur, if 'get_backwards()' has been called at the begin of file border.
	//       Then _current_p == _content - 2 and gets == _content - 1 when the function
	//       get_forward() is called. However, during real lexical analysis, get_backward()
	//       shall only be applied during pre-conditions. Pre-conditions are ended with a 
	//       seek to the current position (which is impossibly BOFC. Only then get_forward()
	//       is called.
	//
	if( tmp == BOFC ) { ; /* we are at the beginning, simply do get_forward again */ }
	else if( tmp == x.BLC || tmp == x.EOFC ) {
	    if( x.load_forward() == -1 ) break;
	}

(*) getting a character in forward direction

	const int tmp = x.get_backward();
	//
	// NOTE: In during 'real' analysis tmp == EOFC should never occur. Pre-conditions
	//       are only to be test against, if there is still some input. When EOFC has
	//       occured, then there should be no subsequent pattern.
	//       
	if( tmp == EOFC ) { ; /* we are at the beginning, simply do get_backward again */ }
	else if( tmp == x.BLC || tmp == x.BOFC ) {
	    if( x.load_backward() == -1 ) break;
	}
