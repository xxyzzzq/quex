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
SHIFT
SET P2=%1
SHIFT
SET P3=%1
SHIFT
SET P4=%1
SHIFT
SET P5=%1
SHIFT
SET P6=%1
SHIFT
SET P7=%1
SHIFT
SET P8=%1
SHIFT
SET P9=%1
SHIFT
SET P10=%1
SHIFT
SET P11=%1
SHIFT
SET P12=%1
SHIFT
SET P13=%1
SHIFT
SET P14=%1
SHIFT
SET P15=%1
SHIFT
SET P16=%1
SHIFT
SET P17=%1
SHIFT
SET P18=%1
SHIFT
SET P19=%1
SHIFT
SET P20=%1
SHIFT
SET P21=%1
SHIFT
SET P22=%1
SHIFT
SET P23=%1
SHIFT
SET P24=%1
SHIFT
SET P25=%1
SHIFT
SET P26=%1
SHIFT
SET P27=%1
SHIFT
SET P28=%1
SHIFT
SET P29=%1
SHIFT
SET P30=%1
SHIFT

python "%QUEX_PATH%\quex-exe.py" %P1% %P2% %P3% %P4% %P5% %P6% %P7% %P8% %P9% %P10% %P11% %P12% %P13% %P14% %P15% %P16% %P17% %P18% %P19% %P20% %P21% %P22% %P23% %P24% %P25% %P26% %P27% %P28% %P29% %P30%


