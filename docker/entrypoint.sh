#!/bin/bash

set -e

cmd="$@"

if [ $# = 0 ]; then
    cmd="sleep infinity"
fi

/workspace/tornado-file-server/run.sh

exec $cmd
