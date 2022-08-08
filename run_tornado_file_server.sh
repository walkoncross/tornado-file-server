#!/bin/bash

# python3 --version
root_dir=./

# echo "number of args: $#"

if [[ $# -gt 0 ]]; then
    root_dir=$1
fi

port=8899
max_items=50

ip=`python -m tornado_file_server.get_ip`

echo "root_dir: $root_dir"
echo "IP: $ip"
echo "Port: $port"

echo "===> Open your browser and input: $ip:$port or localhost:$port"
# nohup python3 tornado_file_server.py 
#     --log-file-prefix=./log 
#     --port=$port \
#     --max-items=$max_items \
#     $root_dir \
#     &

nohup python -m tornado_file_server.serving \
    --port $port \
    --max-items $max_items \
    $root_dir \
    &
