def do():
    """Generate code to iterate over the input stream until

           -- A character occurs not in CharacterSet, or
           -- [optional] the 'LexemeEnd' is reached.

    That is, simplified:
                             input in Set
                             .--<--.
                            |      |  LexemeEnd
                            |      +----->------> (Exit)
                          .----.   |
               --------->( Loop )--+----->------> Exit
                          '----'       input 
                                     not in Set
        
    At the end of the iteration, the 'input_p' points to (the begin of) the
    first character which is not in CharacterSet (or the LexemeEnd).

            [i][i][i]..................[i][i][X][.... 
                                             |
                                          input_p
            
    During the 'loop' possible line/column count commands may be applied. To
    achieve the iteration, a simplified pattern matching engine is implemented:



              transition
              map
              .------.  
              |  i0  |----------> Terminal0: CommandList0   
              +------+
              |  i1  |----------> Terminal1: CommandList1   
              +------+
              |  X2  |----------> TerminalInconsiderate: input_p--; goto TerminalExit;
              +------+
              |  i2  |----------> Terminal2: CommandList2
              +------+

    """

