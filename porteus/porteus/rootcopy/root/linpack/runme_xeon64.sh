#!/bin/sh

export KMP_AFFINITY=nowarnings,compact,1,0,granularity=fine

./xlinpack_xeon64 lininput_xeon64
