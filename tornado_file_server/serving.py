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


def define_arg_parser():
    """define_arg_parser

    Returns:
        ArgumentParser: _description_
    """
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
        '-m', "--items-per-page",
        dest='items_per_page', type=int, default=50,
        help="max items to show in each page. Default: 50"
    )
    parser.add_argument(
        '-vm',
        "--view-mode",
        dest='view_mode', type=str, default='list',
        help="view mode, ['list', 'preview']. Default: 'list'"
    )
    parser.add_argument(
        '-ipr', "--items-per-row",
        dest='items_per_row', type=int, default=4,
        help="number of items per row for media preview mode. Default: 4"
    )
    parser.add_argument(
        '-iw', "--image-width",
        dest='image_width', type=int, default=256,
        help="image width for media preview mode. Default: 256"
    )

    return parser


def serving():
    """serving function, start serving
    """
    arg_parser = define_arg_parser()
    args = arg_parser.parse_args()

    print(u'===> args: \n', args)

    # define_args()
    # args.parse_command_line()

    if not is_python3():
        args.dir = args.dir.decode('utf-8')  # convert into unicode

    logging.basicConfig(filename=args.log_path,
                        encoding='utf-8', level=logging.INFO)

    logging.info(u"===> args: {}".format(args))
    logging.info(u'===> Current Working Dir: {}'.format(args.dir))
    generate_404_html(args.dir)

    start_server(
        args.dir,
        port=args.port,
        items_per_page=args.items_per_page,
        view_mode=args.view_mode,
        items_per_row=args.items_per_row,
        image_width=args.image_width
    )


if __name__ == '__main__':
    # sys.exit(main())
    serving()
