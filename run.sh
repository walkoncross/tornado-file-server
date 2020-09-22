#!/bin/bash

port=8899
root_dir=./
max_items=50

echo "===> Open your browser and input: <server_ip>:$port or localhost:$port"
nohup python2 tornado_file_server.py --log-file-prefix=./log --port=$port --max-items=$max_items --dir=$root_dir &

