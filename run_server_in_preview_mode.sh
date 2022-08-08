#!/bin/bash

# python3 --version
root_dir=./

# echo "number of args: $#"

if [[ $# -gt 0 ]]; then
    root_dir=$1
fi

view_mode=preview
port=8899
items_per_page=50
items_per_row=4
image_width=256

ip=`python -m tornado_file_server.get_ip`

echo "root_dir: $root_dir"
echo "IP: $ip"
echo "Port: $port"

echo "===> Open your browser and input: $ip:$port or localhost:$port"

python -m tornado_file_server.serving \
    --port $port \
    --items-per-page $items_per_page \
    --view-mode $view_mode \
    --items-per-row $items_per_row \
    --image-width $image_width \
    $root_dir \
    & # run in background
