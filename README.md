# Tornado File Server

Tested Python version: Python 2.7, Python 3.9

1. install tornado: 
```cmd
pip install tornado>=4.5;
```
or just run ./install_tornado.sh

2. git clone this repo;

3. start serving:
```cmd
python -m tornado_file_server.serving --port 8899 _your_root_dir_
```
or just run ./run_tornado_file_server.sh

4. In your internet browser, for local test, put: http://localhost/8899; for public url, put http://_your_binded_public_url_