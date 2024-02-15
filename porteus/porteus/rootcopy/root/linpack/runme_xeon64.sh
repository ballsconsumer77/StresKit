#!/bin/sh

export KMP_AFFINITY=nowarnings,compact,1,0,granularity=fine

# add optional argument for samples and memory size in GB
# use 80% of memory and 100 samples by default
# generate lininput_xeon64 (remove from dir as well)

./xlinpack_xeon64 lininput_xeon64
