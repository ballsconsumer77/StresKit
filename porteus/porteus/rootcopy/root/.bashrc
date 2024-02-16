#!/bin/sh

alias sensors='watch -n 1 sensors coretemp-isa-0000'
alias linpack='function __linpack() { (cd /root/linpack && ./runme_xeon64.sh "$@"); unset -f __linpack; }; __linpack'
alias prime95='(cd /root/prime95 && ./mprime)'
alias ycruncher='(cd /root/ycruncher && ./y-cruncher)'
