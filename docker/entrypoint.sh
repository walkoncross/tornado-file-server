#!/bin/bash

set -e

cmd="$@"

if [ $# = 0 ]; then
    cmd="sleep infinity"
fi

/workspace/tornado-file-server/run.sh
echo 'If no CMD is set, the container will sleep inifinity. Else it will exec the CMD'

exec $cmd
