#!/bin/bash

# python3 --version

port=8899
root_dir=./
max_items=50

ip=`python -m tornado_file_server.get_ip`

echo "===> Open your browser and input: $ip:$port or localhost:$port"
# nohup python3 tornado_file_server.py --log-file-prefix=./log --port=$port --max-items=$max_items $root_dir &

nohup python -m tornado_file_server.serving --port $port --max-items $max_items $root_dir &
