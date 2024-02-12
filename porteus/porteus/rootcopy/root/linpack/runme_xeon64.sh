#!/bin/sh

cd "${0%/*}" || {
  echo "error: failed to change directory"
  exit 1
}

export KMP_AFFINITY=nowarnings,compact,1,0,granularity=fine

./xlinpack_xeon64 lininput_xeon64 | tee lin_xeon64.txt
