#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/009: Lexers on pipes, sockets, and the command line."
    echo "CHOICES:  stdin, stdin-utf8, socket, socket-utf8, command-line, command-line-utf8;"
    exit
fi
cd $QUEX_PATH/demo/C/009

function make_silent() {
    make $1 $2 >& /dev/null
}

function observe() {
    valgrind --leak-check=full -v $1 >& tmp.txt
}

if [[ "$2" == "FIRST" ]]; then
    make_silent clean
fi

case $1 in 
    command-line)
        make_silent lexer-command-line 
        printf "A message\nof a kilobyte\nstarts with a bit.\n" \
               | observe ./lexer-command-line
    ;;
    command-line-utf8)
        make_silent lexer-command-line-utf8
        printf "Сообщение о\nкилобайт начинается\nс одного бита.\nΈνα μήνυμα\nενός kilobyte\nξεκινά με ένα μόνο bit.\n" \
               | observe ./lexer-command-line-utf8
    ;;
    stdin)
        make_silent lexer-stdin 
        cat example-feed.txt | observe ./lexer-stdin 
    ;;
    stdin-utf8)
        make_silent lexer-stdin-utf8 
        cat example-feed-utf8.txt | observe ./lexer-stdin-utf8
    ;;
    socket)
        while ps axg | grep -v grep | grep lexer-socket > /dev/null; do sleep 1; done
        make_silent lexer-socket feed-socket 
        # If there is a 'lexer-socket' application running already => stop it.
        observe ./lexer-socket &
        sleep 1
        ./feed-socket file   example-feed.txt 5 1  >& tmp-feed.txt
        ./feed-socket string bye              1 10 >> tmp-feed.txt 2>&1
        cat tmp-feed.txt
        rm -f tmp-feed.txt
        while ps axg | grep -v grep | grep lexer-socket > /dev/null; do sleep 1; done
    ;;
    socket-utf8)
        while ps axg | grep -v grep | grep lexer-socket > /dev/null; do sleep 1; done
        make_silent lexer-socket-utf8 feed-socket 
        # If there is a 'lexer-socket' application running already => stop it.
        observe ./lexer-socket-utf8 &
        sleep 1
        ./feed-socket file   example-feed-utf8.txt 5 1  >& tmp-feed.txt
        ./feed-socket string bye                   1 10 >> tmp-feed.txt 2>&1
        cat tmp-feed.txt
        rm -f tmp-feed.txt
        while ps axg | grep -v grep | grep lexer-socket > /dev/null; do sleep 1; done
    ;;
esac

python $QUEX_PATH/TEST/show-valgrind.py 

make_silent clean 
