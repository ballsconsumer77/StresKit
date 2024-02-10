#!/bin/bash

main() {
    binary_destination=$1

    wget -O "linpack.tgz" "https://downloadmirror.intel.com/793598/l_onemklbench_p_2024.0.0_49515.tgz"

    if [ ! -e "./linpack.tgz" ]; then
        echo "error: linpack download failed"
        return 1
    fi

    # extract
    7z x ./linpack.tgz
    7z x ./linpack.tar -o"./linpack"

    # version name changes in folder name
    benchmarks_folder=$(find "./linpack" -maxdepth 1 -type d -name "*benchmarks*" -print -quit)

    # copy official binary there as module will be packed later
    cp "$benchmarks_folder/linux/share/mkl/benchmarks/linpack/xlinpack_xeon64" "$binary_destination"

    return 0
}

main "$@"
