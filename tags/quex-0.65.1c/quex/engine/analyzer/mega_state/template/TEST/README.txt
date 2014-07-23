14y04d21d:  Frank-Rene Schaefer

Consideration of Advantage of Recursion:

The advantage of recursion is not considered in detail when the cost of a
possibly combined template is considered. 

                 State 0:                             State 1:             
             .------------.                       .------------.
          .--+---------.  |                    .--+---------.  |
      .-->| Commands A |  |                .-->| Commands A |  |
      |   '------------'  |                |   '------------'  |
      |      |            +-- 'x' --.      |      |            +-- 'x' --.
      |      :            :         |      |      :            :         |
      |      '------------'         |      |      '------------'         |
      |                             |      |                             |
      '-----------------------------'      '-----------------------------'


                                    Combined To


                                   TemplateState
                                  .--------------.
                          .-------+-------.      |
                      .-->| CommandList A |      |
                      |   '---------------'      |
                      |           |              +--- 'x' ----.
                      |           :              :            |
                      |           '--------------'            |
                      |                                       |
                      '---------------------------------------'

CONDITION: -- Two states that transit two itself (RECURSION).
           -- The transition is triggered by the SAME characters.

THEN: The measurement could consider a 'reduced cost', because a uniform target 
      can be implemented. 

BUT: This is considered a special and rare case. When it appears the cost is not
     properly determined. It may be a little higher than justified.

     During code generation, when the command list tree is generated, the 
     optimization is done anyway. It is only not predicted here, when possible 
     combinations are consdired. 

THUS: Only if the CONDITION holds (which is rare) and the decision whether two states
      are combined is close, then a sub-optimal decision may be made.

      As long as the jdugements are not that close, states are combined and the code
      generation will take care of the possible optimizations.
                                 
