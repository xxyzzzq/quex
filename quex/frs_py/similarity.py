word_list = [ "eins", "schifffahrt", "drei", "sieben" ]

def get_motion(Letter, Word, i):
    """Only consider 'motions' of one character. If a letter
       only needs to be move by one position, this is 1/2 an error."""
    LWord = len(Word)
    if i >= LWord - 1:    return 0

    if Word[i] == Letter: return 0

    if i > 0: 
        if Word[i - 1] == Letter: return  -1
    if i < LWord:
        if Word[i + 1] == Letter: return 1
    return 0


def compute(A, B):
    vector = compute_motion_vector(A, B)
    pre_move = -1000
    sum = 0.0
    for i in range(len(A)):
        move = vector[i]
        ## if A == "acht": print "## vector", vector
        if i == len(B):                        sum += (len(A) - len(B)) + prev_move; break
        if   B[i] == A[i]:                     prev_move = 0; continue
        elif move != 0 and move == prev_move:  sum += 1.0 / 2.0
        else:                                  sum += 1.0
        prev_move = move

    if len(B) > len(A): sum += ( len(B) - len(A) ) * 2.0 / 3.0
    return sum


def compute_motion_vector(A, B):
    vector = []
    i = -1
    for letter in A:
        i += 1
        vector.append(get_motion(letter, B, i))

    return vector


for word in ["ains", "zwei", "trei", "sibeen", "vier", "acht", "schiffahrt"]:
    print "%s:" % word
    for candidate in word_list:
        print "    %s: %i" % (candidate, compute(word, candidate))



