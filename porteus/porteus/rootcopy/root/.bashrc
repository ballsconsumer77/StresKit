alias skhelp='cat /root/.skhelp'

linpack() {
    (cd /root/tools/linpack && bash ./runme_xeon64.sh "$@")
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

gsat() {
    (cd /root/tools && ./stressapptest "$@")
}
