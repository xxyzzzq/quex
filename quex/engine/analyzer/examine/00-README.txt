Operation Reduction/Operation Postponing

(C) Frank-Rene Schaefer
-------------------------------------------------------------------------------

ABSTRACT:

This file describes the theoretical background for the process applied by Quex
used to reduce the number of operations or to postpone operations.  The
optimization uses the fact that intermediate values which are developed during
the state transitions are not visible to the outer observer. Instead, only the
values are important that are present upon exit from the state machine.

Figure 1 shows a very simple state machine consisting of four states.  The
dotted lines indicate 'drop-out', i.e. a path that is taken to exit the state
machine.  In the original state machine, as shown in figure 1.a, the content of
'x' is increment upon each transition. When the state machine is left in state
3, for example, three such increments must have taken place. In figure 1.b an
optimized representation of the state machine is shown.  There, value of 'x' is
only determined upon exit.  No increments happen during transitions. Only upon
exit 'x' is assigned the predetermined value. The balance on computational
effort is obvious.

     
         a)          x=x+1        x=x+1        x=x+1
              ( 0 )------->( 1 )------->( 2 )------->( 3 )
                : exit       : exit       : exit       : exit
                :            :            :            :
    
         b)
              ( 0 )------->( 1 )------->( 2 )------->( 3 )
                : exit       : exit       : exit       : exit
                :            :            :            :
               x=0          x=1          x=2          x=3
    
             Figure 1: Original and optimized state machine.
                 
The goal of the described procedure is to remove all operations along state
transitions. However, as is described in a later section, in the case of a 
so called 'mouth state' entry operations may actually be injected in order
to cope with run-time dependencies.

The present analysis requires a state machine which is composed of
'single-entry states'. That is, upon entry into a state the same operations are
executed independently from which the state it is entered or through which
transition.  A single-entry state is shown in figure 2.a. The optimization
transforms the single-entry state machine into a 'multi-entry state machine'.
That is, the operations applied upon entry into a state may be different
dependent from which state or through which transition the entry happens.  A
multi-entry state in shown in figure 2.b.

           a)
     
                  ---------.
                            \                       .-----.
                  -----------+---[ operations ]----( state )----->   
                            /                       '-----'
                  ---------'       
     
           b)
     
                  ---[ operations 0 ]----.
                                          \         .-----.
                  ---[ operations 1 ]------+-------( state )----->  
                                          /         '-----'
                  ---[ operations 2 ]----'       


      Figure 2: Two approaches of state modelling: a) Single entry state. 
                b) Multi-entry state. 
                
The analysis tries to exploit predictable sequence of operations along state
transitions. This is done by compensating them through a single operation or by
postponing them to a state as late as possible.  Operations are preferably
postponed, because earlier states are passed more often than later states.


-------------------------------------------------------------------------------

BASICS:

Along the transitions of a state machine many different operations may occur
which do not necessarily share the same subject. Some operations determine the
last accepted pattern, the input position to be restored upon acceptance, the
line and column numbers, the checksum value of a lexeme, or the sum of grapheme
widths of the lexeme's characters, and so on. The term 'investigated behavior'
is defined to specify a focus of analysis.  Let the sets of variables which are
associated with an investigated behavior be called DCV.

DEFINITION: DCV -- Description of Concerned Variables

    The 'DCV' of an investigated behavior describes the set of variables which
    are of concern. 

A 'DCV' may be a simple list of variable names or a abstract description such
as 'all variables related to input position storage' where the number of
variables is open.  As a consequence of transitions, a state machine changes
the content of variables. However, not all variables of an DCV are necessarily
relevant for all states. Let the set of required variables be defined as

DEFINITION: RV(i) -- Set of Required Variables

    'RV(i)' defines the variables which are required in state 'i'. The
    variables must be sufficient

      (i)  to implement the investigated behavior upon drop-out and
      (ii) to develop the DCV settings of all successor states.

In contrast to 'DCV', the set of variables in 'RV(i)' must be concrete.
Instead of the loose statement 'all variables related to input position
storage', the specific variables must be specified. 

'RV(i)' can be determined by *back-propagation* of needs. A state which
requires a specific variable tags all of its predecessor states with this
requirement. That is, if a state 'k' requires a variable 'x', then 'x is
element of 'RV(i)' for every state 'i' that lies on the path to 'k'.

Assume for example, that the lexeme length is not required in a terminal. Then
any operation contributing to the computation of the lexeme length is
redundant.  No state on a path to this terminal is required to perform lexeme
length related operations, except that another successor state requires it.
Let setting of required variables be defined as follows.

DEFINITION: V(i) -- Setting of RV(i)

    The term 'V(i)' represents the settings of all required variables 'RV(i)'
    after a state 'i' is entered and before it transits further. 
    
An elementary unit that modifies the content of a variable is called an
'operation', as defined here:

DEFINITION: op(i) -- Operation 

    A modification to a one or more variable of 'RV(i)' upon entry into a state
    'i' is called an operation 'op(i)'. 
    
With 'V(h)' as the setting before entry into a state 'i' and 'V(i)' as the
setting in state 'i' the operation 'op(i)' describes the modification by 

                         V(i) = op(i)(V(h))

With the aforementioned definitions, the investigated behavior can be defined
precisely.

DEFINITION: Investigated Behavior 

   The 'investigated behavior' determines the scope of analysis. It is
   specified by a description of concerned variables 'DCV', the required
   variables 'RV(i)' for each state 'i', the related operations 'op(i)' and
   their *nominal behavior*.
    
A 'nominal behavior' defines what needs to happen during the state machine
transitions.  For example, the nominal behavior for line number counting is
that the line number variable should be increased upon newline and remain the
same upon the occurrence of any other character. 

-------------------------------------------------------------------------------

LINEAR STATES AND MOUTH STATES:

Two central concepts are required for the further discussion: 'linear states' and 'mouth
states'.  They are defined in the paragraphs to follow. 

DEFINITION: Linear State

    A linear state is a state that is entered only from one predecessor state.

The concept of a linear state is shown in figure 3. The operation 'op(i)' works
on the 'V(k)' before entry and produces 'V(i)'. Note, that a linear state
may have transitions to multiple successor states, but only on predecessor state.


                                                      .---> 
                                                     /
                                                   .-.
                      --------[ op(i) ]---------->( i )---> 
                     V(k)              V(i)    '-'

                    Figure 3: The concept of a linear state.


DEFINITION: Mouth State

    A mouth state is a state that is entered from more than one predecessor 
    state. 
    
Figure 4 displays the concept of a mouth state and the development of the
'V(i)' based on the DCVs of predecessor states.

                  ------>--.  
                 V(a)       \ 
                             \                       .-.
                  ------>-----+---[ op(i) ]---------( i )---> 
                 V(b)        /                 V(i)  '-'
                            /
                 ...       :
                  ------>--'
                 V(z)

                    Figure 4: The concept of a mouth state.

In a linear state the 'V(i)' can be determined based on the predecessor's
DCV and the 'op(i)'

            V(i) = op(i)(V(k))                                          (1)

with 'k' as the one and only predecessor state. If 'V(k)' is known, then
'V(i)' of a linear state is known off-line purely from the consideration of
the state machine.  In a mouth state 'V(i)' is be determined depending on the
state from where the transition originates.

                    /  op(i)(V(a))  if entry from state 'a'
                    |  op(i)(V(b))  if entry from state 'b'             (2)
            V(i) =  |   ...
                    |  
                    \  op(i)(V(z))  if entry from state 'z'

Later procedures rely on stored reference copies of variables. Those values
are stored in so called 'auxiliary variables' as defined below.

DEFINITION: A, A(v) -- Auxiliary Variables

   The term auxiliary variable 'A(v)' specifies a variable that may store the
   a 'snapshot' of a variable 'v'-s content upon entry into a mouth state. 
   
   'A' names the set of all auxiliary variables.

Let 'recipe' be the procedure to determine the DCV in a state without
considering any previous operation. That is, if for all states all recipes are
known, then all operations along the state machine transitions can be removed.
Let the term recipe be defined as follows.

DEFINITION: R(i,k), R(i) -- Recipe 

   Let 'R(i,k)' indicates the 'recipe' to determine 'V(i)' upon entry into a
   state 'i' from a predecessor state 'k'.  
   
   A recipe consists of two components: A procedure to determine 'V(i)' and a
   'snapshot map'. 
   
   The procedure tells how to compute the variables of 'RV(i)' which is derived
   from the operation 'op(i)' and 'R(k)'.  It maps

        (h(i), A) ---> V(i)                                             (3)

   with 'h(i)' signifying the hidden variables of state machine and 'A' the
   set of auxiliary variables. 
   
   The snapshot map associates an auxiliary variable with the state index
   where a snapshot of its value has been stored in 'A(v)', i.e.
   
        snapshot map:  v ---> state 'i' where 'A(v) = v' happend.
   
   Let 'R(i)' indicate the recipe which appears to the successor states of
   state 'i'.

Hidden variables are all variables of the state machine other than the 'state'.
A lexical analyzer state machine has, for example the lexeme start position,
the buffer limits, the stream position, etc. as hidden variable. The state
in which an auxiliary variable takes a 'snapshot' is crucial when comparing
two recipes. Even if they provide the same procedure, if they rely on stored
values at different places, then they cannot be equal.

STATEMENT:

   If the snapshot maps of two recipes are unequal, then the two recipes
   are unequal.

The fundamental difference between 'R(i)' and 'V(i)' is that the former describes
a procedure and the latter represents the values which are produced.

The simplest form of a recipe is the setting with constant values.  For
example, at a state entered by the newline character the recipe for 'column
number' may be 'column number = 0', because a new line begins. The advantage of
recipes is demonstrated figure 5.


    a)        
            'accept=10'        'accept=12'        
       ... ------------>( 1 )-------------->( 2 )----> ...
                          :                   :
                    goto T(accept)      goto T(accept)

    b) 
       ... ------------>( 1 )-------------->( 2 )----> ...
                          : 'accept=10'       : 'accept=12'              
                          :                   :
                      goto T10            goto T12

     Figure 5: Equivalent state sequences. a) Relying on operations along
               transitions. b) DCVs determined by recipes.

In figure 5.a operations are executed at each transition step. They assign
identifiers to the last acceptance variable 'accept'. This assignment happens
even if states '1' and '2' are passed by and later states may detect another
acceptance. Upon drop-out from state 1 or 2 a conditional goto to a terminal is
applied based on the setting of 'accept'. 

In figure 5.b the operations along transitions are completely removed. The
recipes determined the acceptance a priori, so that a direct goto to the
correspondent terminal can be applied.  Clearly, the second approach requires
no computational effort during transitions and lesser effort upon drop-out.

With the concepts of this section, the overall goal can be formulated. The
analysis transforms the given single-entry state machine based on operations
into a multi-entry state machine based on recipes. Observing only the entry and
exit, the changes to the DCV must comply to the nominal behavior. 

-------------------------------------------------------------------------------

BASICS ON PROPAGATION OF RECIPES

A recipe for one state is the basis for the development of the recipe of its
successor state. For a linear state, equation (1) described how 'V(i)' is
determined from the predecessor's 'V(k)' and the entry operation 'op(i)'. If
'V(k)' can be determined by a recipe 'R(k)', then 'V(i)' becomes

                     V(i) = op(i)(R(k))                                     (4)

Since, a recipe 'R(k)' is already independent of operations along transitions,
the recipe for 'V(i)' becomes nothing else than the expression that
determines it. That is,

                     R(i) = { op(i)(R(k)) }                                 (5)
                 
The above definition tells that recipes can only come from recipes. An
important step towards the answer where the first recipe comes from is the
concept of a 'historyless recipe'. It is based on the concept of 
'historyless variables'.

DEFINITION: HLV(i) -- Historyless Variables

   The set of historyless variables in a state 'i' is given by 
 
                        HLV(i) \subset RV(i)                                (6)

   For all 'v in HLV(i)' determined by 'v by op(i)' it holds that 

                   v not a function of V(k) forall 'k' in P(i)              (7)

   where 'P(i)' is the set of predecessor states of 'i'.

A variable can only be history less, if 'op(i)' assigns a constant to it which
is independent of previous states or paths.  When history becomes important,
then the development of a variable setting must be accomplished at
'run-time' using system memory, that is auxiliary variables.

DEFINITION: HLR(i) -- Historyless Recipe

   For a given state 'i' the 'HLR(i)' expresses the effect of 'op(i)' on the
   set of required variables 'RV(i)' in isolation of previous history.  That
   is, for each variable 'v in RV(i)' it holds

                    /   v by op(i)    for v in HLV(i)                
                v = |                                                       (8)
                    \   A(v)          else.

The historyless recipe is only correct, if 'A(v)' contains the correct value of
'v' upon entry into state 'i' after 'op(i)' has been applied for all 'v not in
HLV(i)'.  A historyless recipe can be considered as start for analysis if the
set of required variables is equal to the set of historyless variables.
Accordingly, a spring can be defined.

DEFINITION: Spring

    A state 'i' where all required variables 'RV(i)' can be determined by 
    the historyless recipe 'HLR(i)' is called a spring. It holds

                          RV(i) = HLV(i)

    The procedure of recipe 'R(i)' for a spring state is determined by
    
                          R(i) := HLR(i)

    The relates snapshot map is empty, since it does not rely on any value
    stored at run-time.

In other words, for a spring there is no 'v' determined by 'A(v)' as shown in
equation 8.  In equation 5 it is demonstrated how a recipe 'R(i)' is derived
from a predecessor's recipe 'R(k)' and a state 'i'-s operation 'op(i)'. This
procedure is defined here as 'accumulation'.

DEFINITION: Accumulation

    Given a state 'i', its predecessor state 'k', the entry operation 'op(i)'
    the predecessor's recipe 'R(k)', the recipe to 'R(i,k)' is equivalent
    to the concatenated operations of 'op(i)' and 'R(k)'.

    The snapshot map of 'R(i)' is equal to the snapshot map of 'R(k)'.

    A prerequisite for accumulation is that 'R(k)' of the predecessor is 
    determined.

EXAMPLE:
                  op(b)=        op(c) =      op(d) =
                    x=x+1         x=x+1         x=x+1        
            ( a )-------->( b )-------->( c )-------->( d )--------> ...


                  Figure 6: A sequence of linear states.


Figure 6 displays an example of an DCV containing a single variable 'x'. The
operations 'op(i)' upon transition are 'x=x+1' for all states. That is 'x' is
incremented by 1 at each step. Let the 'A(x,a)' signify 'A(x)' as it was
assigned upon entry into state 'a'. This notation combines the recipe's
procedure with its snapshot map. In the above example, the recipe in state 'a'
solely restores what has been stored.

               R(a) = { x := A(x,a) }                                     (6)

The recipe 'R(b,a)' must be equivalent to the concatenated execution of 'op(b)'
and 'R(a)', i.e.

                   { x := A(x,a) }
                   { x := x + 1 }
So, 
               R(b) = { x := A(x,a) + 1 }                                 (7)

This rule applied repeatedly for the states 'c' and 'd' leads to

               R(c) = { x := A(x,a) + 2 }
               R(d) = { x := A(x,a) + 3 }                                 (8)

If the state machine exits at 'a', 'b', 'c' or 'd' the content of 'x' can be
determined without relying on the intermediate operations { x:=x+1 }. This
is shown in figure 7.
 
          ( a )-------->( b )-------->( c )-------->( d )--------> ...
                          :             :             :
                        x=A(x,a)+1    x=A(x,a)+2    x=A(x,a)+3


          Figure 7: Recipes upon exit replace transition operations.

The repeated accumulation of recipes along linear states comes to an end at
mouth states.  Equation (2) described the development of the DCV in mouth
state. Using the concept of a recipe, the equation can be rewritten as

                     /  R(i,p)  if entry from state 'p'
                     |  R(i,q)  if entry from state 'q'
            V(i) = |   ...                                                (9)
                     |  
                     \  R(i,z)  if entry from state 'z'

The applied recipe depends on the origin state of the transition which is only
determined at run-time.  For each variable 'v' in 'RV(i)' there are two
possibilities:

   Homogeneity:   All entry recipes apply the exact same process to
                  determine the variable's content. That is

                  for all q,e in P(i): v by R(i,p) = v by R(i,q) 

   Inhomogeneity: Two or more entry recipes apply a different process
                  to determine the variable's content. That is

                  It exists a p,q where: v by R(i,p) <> v by R(i,q) 

Not that 'R(i,p) <> R(i,q)' is true if the snapshot maps differ. In other
words, two recipe procedures may rely in the same way on a stored value 'A(v)',
but if it has been stored stored in different states, they are still not
the same.

If a variable 'v' is determined homogeneously, then the part of the recipes
that determines it can be overtaken into 'R(i)'. Otherwise, the value must be
computed upon entry and stored in an 'A(v)'. The recipe 'R(i)' must then rely
on 'A(v)'. Let this process be defined as 'interference'.

DEFINITION: Interference

    The process of 'interference' develops a recipe 'R(i)' for a mouth state
    'i' based on entry recipes 
    
                  ER = { op(i)(R(k)): k = 1...N }. 
                  
    Let the entry recipe 'R(i,k)' signify the concatenation of 'op(i)(R(k))'
    where 'R(k)' is the output recipe of predecessor state 'k'. The output
    recipe 'R(i)' depends on the determinacy of 'v', i.e. 

                     /
                     |  v by R(i,p)   if v by R(i,p) = v by R(i,q) for all p,q in P(i)
         v in R(i) = |
                     |  A(v)          else
                     \
    
    where 'P(i)' is the set of predecessor states of 'i'. Foreach 'v' where
    'A(v)' is used an entry operation 'EO(i,k)' is required that stores
    the current value of 'v' in 'A(v)', i.e.

         EO(i,k) = { for each inhomogeneous 'v': A(v) = v by R(i,k) }

In the case of inhomogeneous entry recipes 'A(v)' requires that entry
operations are performed.  That is upon entry from each 'k' into 'i' the
computed value of 'v' is stored in 'A(v)'.  It is the existence of the entry
operations 'EO(i,k)' that induces the necessity of multi-entry states.  

Before interference can be performed, all entry recipes must be determined.  As
long as this is not the case, 'R(i)' cannot be determined. In consequence, no
successor state's recipe can be determined through accumulation. In other
words,  a mouth state blocks any propagation of recipes as long as not all
entry recipes are determined. 

The next section treats the recursive propagation of recipes by accumulation.
It is conceivable, however, that at the begin of analysis all mouth states are
undetermined. Even the initial state may be an undetermined mouth state--so
there are no springs. In that case, the analysis directly starts with a so
called 'dead-lock analysis'. This is the subject of the next section but one.

-------------------------------------------------------------------------------

RECIPE PROPAGATION BY ACCUMULATION

The recipes for states are determined by a 'walk' along linear states. While
linear states have only one entry, they may have transitions to more than one
state. So, the walk along linear states is a recursive 'tree-walk'. The
termination criteria for the walk along linear states is defined as follows.

DEFINITION: Termination criteria for walk along linear states.

    A recursive walk along linear states does not enter the
    state ahead, if 

       (i)   there is no state. The current state is a terminal.
       (ii)  the state ahead is a mouth state.
       (iii) the state ahead is a spring.

The first condition comes natural. The second condition exists, because recipes
cannot be accumulated beyond mouth states. As a direct consequence, the walk
can never go along loops, since a loop requires a state with more than one
entry. The third condition tells that the walk stops where another walk begins
or began.  With these concepts, a first draft of an algorithm for the
determination of recipes can be defined.

          (*) Start.
          (1) springs = initial springs of state machine.
   .----->(2) perform linear walks starting from each spring.
   |          --> determine R(i) along linear states until terminal,
   |              mouth, or springs.
   |          --> entries of mouth states receive entry recipes.
   |      (3) interference in mouth states with complete sets of entry
   |          recipes.
   |      (4) springs = determined mouth states
   '- no -(5) springs empty?
          (*) Stop.

        Algorithm 1: Determination of recipes.

When this algorithm comes to an end, there might be still mouth states with
undetermined entries. The only possible reason for that are circular
dependencies between mouth states. 

PROOF: Unresolved mouth states inhibit circular dependency.

Let 

        U := set of undetermined mouth states after algorithm 1 ended.       (10)

An undetermined mouth state 'i' must have at least one undetermined entry
recipe. Thus one of its predecessor states, let it be named 'k', must be
undetermined. If 'k' is a mouth state, then it must be undetermined.  If state
'k' is a linear state, then its predecessor must be undetermined, the same
holds for k's predecessor, etc. until a mouth state is reached. Thus, the
indeterminacy of a mouth state has its reason in the indeterminacy of at least
one other mouth state--q.e.d. 

Let the fact that a mouth state 'i' is undetermined because of another undetermined
mouth state 'k' be noted as "i depends on k". 

DEFINITION: D(i) -- Dependency Set 

    For a given mouth state 'i' the dependency set 'D(i)' contains all states
    that 'i' requires to be determined, before interference in state 'i' can be
    performed.

If any state 'k' in 'D(i)' depends on another state 'p' then 'i' also depends
on it, i.e.

                   k in D(i) <=> D(k) is subset of D(i)                    (11)

The number of states in a state machine is finite, thus 'D(i)' is finite. Since
every state in 'D(i)' is undetermined, every state in 'D(i)' must depend to
another state that is undetermined. All of those states are equally in 'D(i)'.
Let the number of elements in 'D(i)' be 'n'. If the states of 'D(i)' were
displayed as dots in a plane, and the dependencies between states as arrows,
then there would be 'n' arrows between 'n' dots. This is only
possible, if there is at least one loop (proof is trivial). Thus, 

         U is not empty <=> there is at least one circular dependency      (12)

q.e.d.

It is this circular dependency which prevents algorithm 1 from being a complete
solution. The following section discusses a solution for these cases where 
the deterministic propagation of recipes failed.

-------------------------------------------------------------------------------

DEAD-LOCK STATES

Interference can only be performed, if all entry recipes of a mouth state are
determined. Loops in the state machine graph, however, cause circular
dependencies.  Figure 8 shows an example, where the two states 1 and 2 mutually
block each other. The recipe R(1) for state 1 cannot be determined because it
requires R(2) which is undetermined. However, before R(2) from state 2 can be
determined, R(1) must be present. Both states, 1 and 2, cannot perform an
interference, because they are missing an entry recipe. 

                                       R(1)
                          R(0)     .---->----.
                    ( 0 )------>( 1 )       ( 2 )
                                   '----<----'
                                       R(2)

           Figure 8: A dead-lock in mouth states 1 and 2.

DEFINITION: Dead-Lock State

   A dead-lock state is a mouth state that contains at least one undetermined
   entry. Due to the missing entry recipe interference may not be performed
   for that state.

DEFINITION: Horizon

   Let the term 'horizon' H indicate the subset of dead-lock states that have
   at least one determined entry.

The name 'horizon' is chosen because it defines the border of determination.
Beyond that begins the realm of dead-locks. Figure 9 shows a horizon state
which contains one determined entry and another undetermined entry.

                         R(a) -->--.
                                    \
                                     +---[ op(i) ]---( i )----> R(i)
                                    /
                     R(b) = ? -->--'

          Figure 9: A mouth state with a determined entry 'R(a)' and 
                    an undetermined entry 'R(b)'.

The process of propagation of recipes ended with dead-lock states. In order
to understand the nature of dead-lock states better, it makes sense to briefly
review this process. 

The init state is the first state that is entered. It has at least one recipe
'R(outside)', i.e. the recipe to be applied when coming from 'outside' the
state machine. If it has another entry that is undetermined, then the init
state becomes a horizon state. If the init state has no other entry, then it is
a spring and determined recipes are propagated through accumulation.
Accumulation ends with the determination of an entry into a mouth state. If the
reached mouth state has ends up with determined entries, then a determined
recipe is propagated until a terminal or another mouth state is reached. If a
mouth state is reached where not all entries are determined, then its output
recipe is undetermined.  Consequently, all successor states of that state are
undetermined. It follows the following statement.

STATEMENT: 

   A dead-lock state can only reached by a path that guides through a horizon
   state. 

In other words, the horizon states are the entry points to the realm of
dead-lock states.  The entry happens through the determined entry of a horizon
state--in the example of figure 9 it is 'R(a)'. On the other hand, the output
of a dead-lock state is undetermined, so any mouth state it reaches is
undetermined. Any state before a horizon state is determined. So, the output
of a dead-lock state never influences a state before the horizon. 

STATEMENT:

    Non-dead-lock states are never reached by dead-lock states.

This has an importance consequence: The snapshot maps of recipes before a
horizon state never contain state indices of states in the horizon or beyond.
This has an important consequence. A procedure at an entry into a mouth state
is only overtaken into the output recipe, if it is homogeneous with the
according procedure at all other entries. With one recipe being determined, the
set of possible output recipes becomes restricted. 

Let 'R(i,k)' be a determined entry into a horizon state. Then, for all 'v'
where 'v by R(i,p) = R(i,k)' with 'p in P(i)' the output recipe 'v by R(i) = v
by R(i,k)'. For all other 'v' an entry operation must store the value of 'A(v)
= v by R(i,p)' and the output recipe is 'A(v)'. Briefly, there are two alternatives
               /
               | v by R(i,k) if R(i,k) = R(i,p) for all p in P(i)
   v by R(i) = |
               | A(v)
               \ 

The interesting point lies in the snapshot maps states. If 'v by R(i)' is determined
by 'A(v)' then the snapshot map contains 'v -> i', that is the snapshot of 'v'
has been stored in 'A(v)' at state 'i'. If 'v by R(i)' is determined by 'b by
R(i,k)' then only snapshot map of 'R(i,k)' is transferred to 'R(i)'. State 'k'
however, is a state before the horizon. An incoming recipe 'op(i)(R(p))' comes
from a state after the horizon. If it relies on restored values of 'A(v)' then
those are from after the horizon. Thus, snapshot maps between the determined
entry and later incoming snapshot maps will never be equal. The EO remain
necessary.

Since any type of interference requires
homogeneity for a procedure 'v by R(i,k)' for all 'k in P(i)'

Interference offers entry operations which are performed at run-time. If an
entry such as 'R(b)' cannot be determined at analysis time, then at least one
can assume the entry recipe 'R(i,b)' to compute on real values at run-time and
store those.

          EO(i,b) = { for each v: A(v) = v by op(i)(V(b)) }

That is, assign to 'A(v)' the value computed for 'v' by applying 'op(i)' on the
setting of variables in state 'b'. Since, every value is stored upon entry,
the output recipe can be specified as a pure 'restore recipe':

         v by R(i) = { v = A(v) }

If 'op(i)' stores a constant in a 'v', then that 'v' can still be treated on
the level of recipes. It follows, that the output recipe is exactly the
previously defined historyless recipe 'HLR(i)'. The presented solution of entry
operations storing snapshots in auxiliary variables and recipes that rely on
stored values is the most general solution--a solution that never fails to be
correct. The above concepts allow to determine an output recipe for a mouth
state with undetermined entries.

DEFINITION: Run-Time Interference

    The process of 'run-time interference' develops a recipe 'R(i)' for a mouth
    state 'i' in the presence of undetermined entry recipes. The set of entry
    recipes becomes

            /
            |   op(i)(R(k))  for all k where R(k) is determined
       ER = | 
            |   HLR(i)       for all k where R(k) is undetermined
            \             

    Based on this specification of the entry recipes 'ER' the interference
    procedure as defined before is performed. 

The resulting output recipe 'R(i)' can now be used for propagation. Previously
undetermined mouth state entries become determined. The horizon moves forward
until all mouth states are determined. An entry operation related to an entry
from state 'b' the 'V(b)' term can be replaced by an accumulated recipe 'R(b)'.
What remains is a possible fine-tuning that rids off some storing entry
recipes.

-------------------------------------------------------------------------------

FINE TUNING OF DEAD-LOCK STATES

While the previous discussion provides a general solution, there is still
space for improvement. Figure 10 shows a case where the DCV variable 'x' is
assigned 5 upon entry into state 1 in any case. Storing the value upon entry
and restoring it upon exit, is superfluous. Since the entry recipes are
homogeneous, normal interference may be applied. For the entry from state 1
into state 2, the recipe 'x=6' is sufficient. This section discusses how normal
interference may be applied to further simplify the description while
maintaining correctness.

                                       x=x+1
                          x=5      .---->----.
                    ( 0 )------>( 1 )       ( 2 )
                                   '----<----'
                                       x=5

          Figure 10: Dead-lock group with space for improvement.


By definition, run-time interference can only happen in a state with at least
one determined entry recipe.  Algorithm 1 applied a procedure based on the
deterministic accumulation and interference. Thus, any recipe that resulted
from algorithm 1 is stable and correct.  

In figure 9 a horizon state is shown. Without restricting generality, the entry
recipe 'R(i,b)' represents all inputs into the state which are undetermined
before dead-lock resolution. In the same sense 'R(i,a)' represents all
determined entries. For interference to happen, it must hold

      R(i,a) = R(i,b) with a, b in the set of entry states to state i.

Such is the requirement of homogeneity. The recipe 'R(i,a)' can only depend on
states before the horizon. If it is equal to a recipe 'R(i,b)', then this
recipe also can only depend on states before the horizon. Thus, while 'R(i,b)'
results from interferences and accumulation inside the realm of dead-lock
states, it does not depend on its 'dynamics'. According to the previous
discussion 'R(i,b)' is correct in the general sense. Thus, the derivation
of a resulting recipe is correct and stable in a general sense. 

STATEMENT:

    If entries into a horizon state are homogeneous, then the recipe resulting
    from interference is correct in a general sense. No feedback into the mouth
    state must be further considered. The resulting recipe remains stable.

The output recipe 'R(i)' of the horizon state is determined and correct. After
interference, such a mouth state is no longer part of the horizon. However,
through accumulation of 'R(i)' some other dead-lock mouth states may be
reached. They now have a determined recipe at their entry and become new
horizon states. The procedure of interference and accumulation may be repeated
until no new horizon states with homogeneous entries are found.

-------------------------------------------------------------------------------

