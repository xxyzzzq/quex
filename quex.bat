@ECHO OFF
REM PURPOSE: Calle quex-exe.py like a normal application.
REM
REM Pass up to 30 arguments to quex. Since the very sophisticated .bat files of 
REM Microsoft (TM) do no support more than ten direct accesses to command line arguments,
REM it is necessary to shift. See below.
REM
REM (C) 2008 Frank-Rene Schaefer
REM
SET P1=%1
SET P2=%2
SET P3=%3
SET P4=%4
SET P5=%5
SET P6=%6
SET P7=%7
SET P8=%8
SET P9=%9
SHIFT
SHIFT
SHIFT
SHIFT
SHIFT
SHIFT
SHIFT
SHIFT
SHIFT
SHIFT
SET Q1=%1
SET Q2=%2
SET Q3=%3
SET Q4=%4
SET Q5=%5
SET Q6=%6
SET Q7=%7
SET Q8=%8
SET Q9=%9

python %QUEX_PATH%\quex-exe.py %P1% %P2% %P3% %P4% %P5% %P6% %P7% %P8% %P9% %Q1% %Q2% %Q3% %Q4% %Q5% %Q6% %Q7% %Q8% %Q9% %1% %2%  %3%  %4%  %5%  %6%  %7%  %8%  %9% 

