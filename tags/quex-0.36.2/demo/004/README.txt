----------------------------------------------------------------------------
Benchmarking Suite:
----------------------------------------------------------------------------
(C) 2007-2008 Frank-Rene Schäfer

Abstract:

This suite was created for the purpose to monitor the performance and
performance increase/decrease that accompanies features and design changes.
At the same time, it is hold general in a sense that also other generator
generators can be tested and benchmarked. At the time of this writing 
only 'flex' is tested. The only thing to adapt is the file 'configuration.h'
which contains adaptions for the benchmarking program. If someone is
familiar with his analyzer generator, those things should be extremely
easy to do. Please, feel free to submit adaptions for analyzer generators
that are not yet included.

The source code basically consists of two files:

   lexer.cpp  -- which does the benchmarking.
   report.cpp -- which does the reporting of the results.

Both remain exactly the same for any analyzer generator. As mentioned
before, only the header 'configuration.h' must be adapted.

----------------------------------------------------------------------------
Call Options:
----------------------------------------------------------------------------

This program can be called in three modes:

(1) BENCHMARK: 

    > lexer  file-of-size-1024kB.txt

    Specify file name.  The benchmark may repeat the analysis of this file
    multiple times in order to converge to a stable result. At the end, the
    output reports the number of repetitions. 

    NOTE: The benchmark measures also a 'measuring overhead' which has to be
    subtracted. The overhead can be determined by using the lexer in the
    following modes.

(2) COUNT TOKENS: 

    > lexer  filename.txt

    Counts the number of tokens found in the file 'filename.txt'.  The number
    of tokens is important to determine the measurement overhead.

(3) REFERENCE: 

    > lexer  file-of-size-1024kB.txt  1024  NumberOfTokens RepetitionN

    Computes the same timings as the BENCHMARK, but **does not** do any real
    analysis. Use the data to determine the 'real' values computed by the
    benchmark. 


