alias cputemp='watch -n 1 sensors coretemp-isa-0000'

linpack() {
    (cd /root/tools/linpack && ./runme_xeon64.sh "$@")
}

prime95() {
    (cd /root/tools/prime95 && ./mprime "$@")
}

ycruncher() {
    (cd /root/tools/ycruncher && ./y-cruncher "$@")
}

mlc() {
    (cd /root/tools && ./mlc "$@")
}
