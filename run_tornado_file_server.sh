#!/bin/bash

# python3 --version
root_dir=./

# echo "number of args: $#"

if [[ $# -gt 0 ]]; then
    root_dir=$1
fi

port=8899
items_per_page=50

ip=`python -m tornado_file_server.get_ip`

echo "root_dir: $root_dir"
echo "ip: $ip"
echo "port: $port"
echo "max_items: $max_items"

echo "===> Open your browser and input: $ip:$port or localhost:$port"
# nohup python3 tornado_file_server.py 
#     --log-file-prefix=./log 
#     --port=$port \
#     --max-items=$max_items \
#     $root_dir \
#     &

nohup python -m tornado_file_server.serving \
    --port $port \
    --items-per-page $items_per_page \
    $root_dir \
    & # run in background