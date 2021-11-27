#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
author: zhaoyafei0210@gmail.com
github: https://github.com/walkoncross/tornado-file-server

Starts a Tornado static file/folder server from a given directory.
To start the server in the current directory:
    tornado-file-server ./
Then go to http://localhost:8899 to browse the directory.

Use the --port option to change the port on which the server listens.
    tornado-file-server --port 8899 ./
"""
import logging
from argparse import ArgumentParser
from .tornado_file_server import start_server, generate_404_html
from .python_version import is_python3


if is_python3():
    from builtins import str as unicode


def define_arg_parser(args=None):
    parser = ArgumentParser(
        description=(
            'Start a Tornado server to serve static files and folders out of a '
            'given directory.'))
    # parser.add_argument(
    #     '-f', '--prefix', type=str, default='',
    #     help='A prefix to add to the location from which pages are served.')
    parser.add_argument(
        'dir',
        type=unicode, default='./',
        nargs='?',
        help='(Optional) directory from which to serve files. Default: "./"'
    )
    parser.add_argument(
        '-l', '--log',
        dest='log_path', type=unicode, default='./tornado-file-server.log',
        help='log file path. Default: "./tornado-file-server.log"'
    )
    parser.add_argument(
        '-p', '--port',
        dest='port', type=int, default=8899,
        help='port on which to run the file server. Default: 8899'
    )
    parser.add_argument(
        '-m', "--max-items",
        dest='max_items', type=int, default=50,
        help="max items to show in each page. Default: 50"
    )

    return parser


def serving():
    arg_parser = define_arg_parser()
    options = arg_parser.parse_args()

    print(u'===> args: \n', options)

    # define_options()
    # options.parse_command_line()

    if not is_python3():
        options.dir = options.dir.decode('utf-8')  # convert into unicode

    logging.basicConfig(filename=options.log_path,
                        encoding='utf-8', level=logging.INFO)

    logging.info(u"===> args: {}".format(options))
    logging.info(u'===> Current Working Dir: {}'.format(options.dir))
    generate_404_html(options.dir)

    start_server(
        options.dir,
        port=options.port,
        max_items=options.max_items
    )


if __name__ == '__main__':
    # sys.exit(main())
    serving()
