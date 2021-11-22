#!/bin/bash

# python3 --version

port=8899
root_dir=./
max_items=50

echo "===> Open your browser and input: <server_ip>:$port or localhost:$port"
# nohup python3 tornado_file_server.py --log-file-prefix=./log --port=$port --max-items=$max_items $root_dir &

nohup python tornado_file_server.py --port $port --max-items $max_items $root_dir &
