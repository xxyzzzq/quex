def do(SM, OnDropOutAdr, OnAcceptanceAdr, EngineType, FirstSeparateF=False):
    """________________________________________________________________________

    Generates a 'mini detector', i.e. a small analyzer that verifies or
    falsifies the presence of a pattern. 

        SM              -- The state machine that detects the pattern.
        OnDropOutAdr    -- Address where to jump upon failure.
        OnAcceptanceAdr -- Address where to jump upon success. 
        EngineType      -- Forward or backward lexical analysis.

    If 'FirstSeparateF' is True, the first state is returned separately AND
    it does not increment/decrement the input pointer. It directly considers
    the content of 'input'.
    
    No 'post' or 'pre' context can be considered.
    ___________________________________________________________________________
    """


