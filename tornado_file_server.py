#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
author: zhaoyafei0210@gmail.com
github: https://github.com/walkoncross/tornado-file-server

Starts a Tornado static file/folder  server in a given directory.
To start the server in the current directory:
    tornado-file-server ./
Then go to http://localhost:8888 to browse the directory.
Use the --prefix option to add a prefix to the served URL,
for example to match GitHub Pages' URL scheme:
    tornado-file-server . --prefix=www
Then go to http://localhost:8888/www/ to browse.
Use the --port option to change the port on which the server listens.
"""

from __future__ import print_function
import logging
try:
    from urllib.parse import unquote
except ImportError:
    # Python 2.
    from urllib import unquote

import os
import sys
import time
import os.path as osp

import math
from argparse import ArgumentParser

import tornado.routing
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.escape
import tornado.options

from tornado.options import define, options

# if sys.version.startswith('3.'):
#     from builtins import str as unicode


def define_options():
    define("port", type=int, default=8888, help="Port to listen on")
    define("dir", type=str, default='./',
           help="Directory from which to serve files.")
    define("max_items", type=int, default=50,
           help="Max items to show as in each page.")

# def parse_args(args=None):
#     parser = ArgumentParser(
#         description=(
#             'Start a Tornado server to serve static files and folders out of a '
#             'given directory and with a given prefix.'))
#     parser.add_argument(
#         '-f', '--prefix', type=str, default='',
#         help='A prefix to add to the location from which pages are served.')
#     parser.add_argument(
#         '-p', '--port', type=int, default=8888,
#         help='Port on which to run server.')
#     parser.add_argument(
#         'dir', help='Directory from which to serve files.')
#     return parser.parse_args(args)


content_404_html = '''
<!DOCTYPE html>
<html>
  <body>
    <h1>404 - File or Directory Not Found.</h1>
  </body>
</html>
'''


class FileHandler(tornado.web.StaticFileHandler):
    '''
    Static File Handler
    '''

    def parse_url_path(self, url_path):
        # logging.info('===> self.request.uri: {}'.format(self.request.uri))
        # logging.info('===> self.request.path: {}'.format(self.request.path))
        # logging.info('===> self.request.query: {}'.format(self.request.query))
        # logging.info('===> self.request.headers: {}'.format(self.request.headers))
        # logging.info('===> self.request.body: {}'.format(self.request.body))

        logging.info(
            'GET file path: {}'.format(url_path)
        )

        if not url_path or url_path.endswith('/'):
            logging.info(
                'Cannot find: {}'.format(url_path)
            )
            url_path = osp.join(self.root, '404.html')
            logging.info(
                'Return: {}'.format(url_path)
            )

        if os.path.sep != "/":
            url_path = url_path.replace("/", os.path.sep)

        return url_path


folder_response_header = '''
<meta http-equiv="Content-Type" content="text/html;charset=ISO-8859-1">
<head>
   <style>
      h1, h2, h3, h4 {
      font-family: arial, sans-serif;
      }
      table {
      font-family: arial, sans-serif;
      border-collapse: collapse;
      width: 100%;
      }
      td, th {
      border: 1px solid #dddddd;
      text-align: left;
      padding: 8px;
      }
      tr:nth-child(even) {
      background-color: #dddddd;
      }
   </style>
</head>
'''

folder_content_header_template = '''
<header>
   <h1>Directory: {}</h1>
</header>
'''

folder_content_navi_parent_template = '''
<nav>
   <h4><a href="{}">Go to Parent Dir</a></h4>
</nav>   
'''

folder_content_navi_prev_nohref = '''
   &lt;Prev page
'''

folder_content_navi_next_nohref = '''
   Next page&gt;
'''

folder_content_navi_prev_template = '''
   <a href="{}">&lt;Prev page</a>  
'''

folder_content_navi_next_template = '''
    <a href="{}">Next page &gt;</a>
'''

folder_content_upload_form = '''
<form method="post" enctype="multipart/form-data">
   <div>
      <label for="files">Choose and upload files: </label>
      </br>
      <input type="file" id="files" name="files" multiple>
      </br>
      <button>Upload</button>
   </div>
</form>
'''

folder_content_nothing_found = '''
<h4>Nothing under this directory</h4>
'''

folder_content_table_summary_template = '''
<h4>{} items in total, {} files, {} folders</h4>
<h4>show {} items per page, {} pages</h4>
'''

folder_content_table_header = '''
<table style="width:100%;text-align: left">
<tr>
   <th>Name</th>
   <th>Type</th>
   <th>Modified Time</th>
   <th>File Size</th>
</tr>
'''

folder_content_table_item_template = '''
<tr>
    <td><a href="{}">{}</a></td>
    <td>{}</td>
    <td>{}</td>
    <td>{}</td>
</tr>
'''

folder_content_table_footer = '''
</table>
'''

folder_content_footer = '''
<footer>
  <p><a href="https://github.com/walkoncross/tornado-file-server">github repo</a></p>
</footer>
'''

upload_response_content_header = '''
<h4>OK</h4>
'''

upload_response_content_item_template = '''
<p><em>{}</em> saved into: <em>{}</em></p>
'''


class FolderHandler(tornado.web.RequestHandler):
    '''
    Request Handler to list a files under a directory
    '''

    def initialize(self, max_items_per_page=50):
        '''initialize
        Refer to https://www.tornadoweb.org/en/stable/web.html:

        classtornado.web.RequestHandler(...)[source]
            Base class for HTTP request handlers.

            Subclasses must define at least one of the methods defined in the “Entry points” section below.

            Applications should not construct RequestHandler objects directly and subclasses should not override __init__ (override initialize instead).
        '''
        self.last_request_uri_path = ''
        self.parent_uri_path = ''

        self.local_dir_path = ''
        self.dir_list = []
        self.item_info_list = []

        self.dir_list_len = 0
        self.sub_folder_cnt = 0
        
        self.max_page_id = 1
        self.max_items_per_page = max_items_per_page

        # self.update_dir_info(self.local_dir_path)

    def get_file_mtime(self, path):
        mt = time.localtime(osp.getmtime(path))
        tm_str = time.strftime('%y-%m-%d %H:%M:%S', mt)

        return tm_str

    def get_file_type(self, path):
        ftype = 'unknown'
        if osp.isdir(path):
            ftype = 'DIR'
        elif osp.isfile(path):
            ext = osp.splitext(path)[1]
            if ext:
                ftype = ext
        elif osp.islink(path):
            ftype = 'SYMLINK'

        return ftype

    def get_file_size(self, path):
        sz_unit = ['Byte', 'KB', 'MB', 'GB']

        if osp.isfile(path):
            sz = float(osp.getsize(path))

            unit_idx = 0
            while (sz > 1024):
                sz = sz / 1024
                unit_idx += 1

            sz_str = '%.3f %s' % (sz, sz_unit[unit_idx])
        else:
            sz_str = '-'

        return sz_str

    def update_dir_info(self):
        # unquote quoted self.request.path into local path
        # e.g. "%20" into " "
        logging.info(
            '===> Update folder dir_info: {}'.format(self.request.path)
        )

        self.local_dir_path = tornado.escape.url_unescape(
            self.request.path, plus=False)

        logging.info('===> local_dir_path: {}'.format(self.local_dir_path))

        # full_url = self.request.full_url()
        # logging.info('===> full_url: {}'.format(full_url))

        # use unicode to deal with Chinese characters
        full_local_dir_path = unicode(os.getcwd()) + self.local_dir_path
        #logging.info("===>full_local_dir_path: {}".format(full_local_dir_path))

        if not self.request.path or self.request.path == '/':
            self.parent_uri_path = self.request.path
        else:
            if self.request.path.endswith('/'):
                self.parent_uri_path = osp.dirname(self.request.path[:-1])
            else:
                self.parent_uri_path = osp.dirname(self.request.path)

        self.dir_list = os.listdir(full_local_dir_path)
        # os.listdir() returns a list in arbitray order on Linux filesystem

        if sys.platform is not 'win32':
            self.dir_list = sorted(self.dir_list, key=lambda s: s.lower())

        self.dir_list_len = len(self.dir_list)
        self.item_info_list = []
        self.max_page_id = 1
        # self.last_request_uri_path = self.request.path
        self.sub_folder_cnt = 0

        if self.dir_list_len > 0:
            #logging.info("===>Found {} files/folders".format(self.dir_list_len))
            self.max_page_id = int(math.ceil(
                self.dir_list_len / float(self.max_items_per_page)))

            for item in self.dir_list:
                item_local_dir_path = osp.join(full_local_dir_path, item)
                # logging.info(u'item local path:', item_local_dir_path)
                if osp.isdir(item_local_dir_path):
                    self.sub_folder_cnt += 1

                modify_time = self.get_file_mtime(item_local_dir_path)
                #logging.info('modify time: {}'.format(modify_time))
                file_type = self.get_file_type(item_local_dir_path)
                #logging.info('file type: {}'.format(file_type))
                file_size = self.get_file_size(item_local_dir_path)
                #logging.info('file size: {}'.format(file_size))

                item_utf = item.encode('utf-8')

                item_url = tornado.escape.url_escape(item_utf, plus=False)
                item_url = osp.join(self.request.path, item_utf)
                # logging.info('===> link url: {}'.format(item_url))
                #item_url = self.reverse_url(item)

                self.item_info_list.append(
                    (item_url, item_utf, modify_time, file_type, file_size)
                )

    def get(self, path):
        # logging.info('===> self.path_args: {}'.format(self.path_args))
        # logging.info('===> self.path_kwargs: {}'.format(self.path_kwargs))

        # logging.info('===> self.request.uri: {}'.format(self.request.uri))
        # logging.info('===> self.request.path: {}'.format(self.request.path))
        # logging.info('===> self.request.query: {}'.format(self.request.query))
        # logging.info('===> self.request.headers: {}'.format(self.request.headers))
        # logging.info('===> self.request.body: {}'.format(self.request.body))

        # if path is '':
        #     path = '/'

        logging.info(
            'GET folder uri: {}'.format(self.request.uri)
        )

        if self.request.path != self.last_request_uri_path:
            logging.info(
                '===> Last request uri path: {}'.format(self.last_request_uri_path)
            )
            self.update_dir_info()

        page_id = self.get_query_argument(name="page_id", default='1')

        logging.info(
            'page_id: {}'.format(page_id)
        )

        try:
            page_id = int(page_id)
        except:
            page_id = 1

        logging.info(
            'max_page_id: {}'.format(self.max_page_id)
        )

        if page_id > self.max_page_id:
            page_id = 1

        logging.info(
            'page_id after check: {}'.format(page_id)
        )

        content = folder_content_header_template.format(self.local_dir_path)
        content += folder_content_navi_parent_template.format(self.parent_uri_path)
        content += folder_content_upload_form

        if self.dir_list_len < 1:
            content += folder_content_nothing_found
            # logging.info(content)
        else:
            content += folder_content_table_summary_template.format(
                self.dir_list_len, 
                self.dir_list_len - self.sub_folder_cnt, 
                self. sub_folder_cnt,
                self.max_items_per_page, 
                self.max_page_id
            )

            prev_page_id = page_id-1
            if prev_page_id < 1:
                content += folder_content_navi_prev_nohref
            else:
                content += folder_content_navi_prev_template.format(
                    path+'?page_id='+str(prev_page_id))

            next_page_id = page_id+1
            if next_page_id > self.max_page_id:
                content += folder_content_navi_next_nohref
            else:
                content += folder_content_navi_next_template.format(
                    path+'?page_id='+str(next_page_id))

            #logging.info("===>Found {} files/folders".format(self.dir_list_len))
            folder_content_table = folder_content_table_header

            start_idx = self.max_items_per_page * (page_id-1)
            end_idx = min(self.max_items_per_page * page_id, self.dir_list_len)

            for i in range(start_idx, end_idx):
                item_info = self.item_info_list[i]
                # logging.info(
                #     'item_info: {}'.format(item_info)
                # )
                folder_content_table += folder_content_table_item_template.format(
                    item_info[0],
                    item_info[1],
                    item_info[2],
                    item_info[3],
                    item_info[4]
                )

            folder_content_table += folder_content_table_footer
            content += folder_content_table

        # content = folder_content_navi_template.format(self.local_dir_path, parent_uri_path)
        # content += folder_content_upload_form

        content += folder_content_footer
        self.write(folder_response_header + content)

        self.last_request_uri_path = self.request.path

    def post(self, path):
        # logging.info('===> self.path_args: {}'.format(self.path_args))
        # logging.info('===> self.path_kwargs: {}'.format(self.path_kwargs))

        # logging.info('===> self.request.uri: {}'.format(self.request.uri))
        # logging.info('===> self.request.path: {}'.format(self.request.path))
        # logging.info('===> self.request.query: {}'.format(self.request.query))
        # logging.info('===> self.request.headers: {}'.format(self.request.headers))
        # logging.info('===> self.request.body: {}'.format(self.request.body))
        logging.info(
            'POST : {}'.format(self.request.uri)
        )

        response_content = upload_response_content_header

        for field_name, files in self.request.files.items():
            for info in files:
                filename, content_type = info["filename"], info["content_type"]
                body = info["body"]
                logging.info(
                    'POST "%s" "%s" %d bytes', filename, content_type, len(
                        body)
                )

                save_filename = osp.join(path, osp.basename(filename))
                if osp.isfile(save_filename):
                    i = 0
                    fn, ext = osp.splitext(save_filename)

                    while osp.isfile(save_filename):
                        i += 1
                        save_filename = fn + '.{:03d}'.format(i) + ext

                fp = open(save_filename, 'w')
                fp.write(body)
                fp.close()

                response_content += upload_response_content_item_template.format(
                    filename, save_filename)

        self.write(response_content)


class File_matcher(tornado.routing.Matcher):
    def match(self, request):
        full_local_dir_path = unicode(
            os.getcwd()) + tornado.escape.url_unescape(request.path, plus=False)
        # logging.info(u'full_local_dir_path in File_matcher:', full_local_dir_path)
        if osp.isfile(full_local_dir_path):
            return {}
        else:
            return None


class Folder_matcher(tornado.routing.Matcher):
    def match(self, request):
        full_local_dir_path = unicode(
            os.getcwd()) + tornado.escape.url_unescape(request.path, plus=False)
        # logging.info(
        #     u'full_local_dir_path in Folder_matcher:{}'.format(full_local_dir_path))
        if osp.isdir(full_local_dir_path):
            return {}
        else:
            return None


# class POSTHandler(tornado.web.RequestHandler):
#     def post(self):
#         for field_name, files in self.request.files.items():
#             for info in files:
#                 filename, content_type = info["filename"], info["content_type"]
#                 body = info["body"]
#                 logging.info(
#                     'POST "%s" "%s" %d bytes', filename, content_type, len(
#                         body)
#                 )

#                 save_filename = osp.join(save_dir, osp.basename(filename))
#                 # if osp.isfile(save_filename)
#                 fp = open(save_filename, 'bw')
#                 fp.write(body)
#                 fp.close()

#         self.write("OK")


# @tornado.web.stream_request_body
# class PUTHandler(tornado.web.RequestHandler):
#     def initialize(self):
#         self.bytes_read = 0

#     def data_received(self, chunk):
#         self.bytes_read += len(chunk)

#     def put(self, filename):
#         filename = unquote(filename)
#         mtype = self.request.headers.get("Content-Type")
#         logging.info('PUT "%s" "%s" %d bytes',
#                      filename, mtype, self.bytes_read)
#         self.write("OK")


# def mkapp(prefix=''):
#    if prefix:
#        path = '/' + prefix + '/(.*)'
#    else:
#        path = '/(.*)'
#
#    #logging.info("os.getcwd() = : {}".format(os.getcwd()))
#    application = tornado.web.Application([
#        (path, FileHandler, {'path': os.getcwd()}),
#        (r"/content/(.*)", tornado.web.StaticFileHandler, {"path": os.getcwd()}),
#    ], debug=True)
#
#    return application
#
# def start_server(prefix='', port=8888):
#    app = mkapp(prefix)
#    app.listen(port)
#    tornado.ioloop.IOLoop.instance().start()


def start_server(port=8888, max_items=50):
    path = '/(.*)'

    file_app = tornado.web.Application(
        [
            (path, FileHandler, {'path': os.getcwd()}),
        ],
        debug=True
    )

    folder_app = tornado.web.Application(
        [
            (path, FolderHandler, {"max_items_per_page": max_items}),
        ],
        debug=True)

    error_app = tornado.web.Application(
        [
            (path, tornado.web.ErrorHandler, {"status_code": 404}),
        ],
        debug=True)
    # post_app = tornado.web.Application(
    #     [
    #         (r"/post", POSTHandler),
    #         # (r"/(.*)", PUTHandler)
    #     ]
    # )

    router = tornado.routing.RuleRouter([
        tornado.routing.Rule(File_matcher(), file_app),
        tornado.routing.Rule(Folder_matcher(), folder_app),
        tornado.routing.Rule(tornado.routing.AnyMatches(), error_app),
        # tornado.routing.Rule(tornado.routing.PathMatches(r"/post"), post_app)
        # tornado.routing.Rule(tornado.routing.PathMatches(path + r"/post"), post_app)
    ])

#    router = tornado.routing.RuleRouter([
#        tornado.routing.Rule(tornado.routing.PathMatches("/app1.*"), file_app),
#        tornado.routing.Rule(tornado.routing.PathMatches("/app2.*"), folder_app)
#    ])

    server = tornado.httpserver.HTTPServer(router)
    server.listen(port)
    tornado.ioloop.IOLoop.current().start()


def generate_404_html(save_dir):
    fp = open(osp.join(save_dir, '404.html'), 'w')
    fp.writelines(content_404_html)
    fp.close()


def main(args=None):
    # args = parse_args(args)

    # logging.info("===> args: {}".format(args))
    # os.chdir(args.dir)
    # logging.info('===> Current Working Dir: ', os.getcwd())
    # generate_404_html(args.dir)
    # #logging.info('Starting server on port {}'.format(args.port))
    # start_server(prefix=args.prefix, port=args.port)

    define_options()
    options.parse_command_line()

    logging.info("===> args: {}".format(options))
    os.chdir(options.dir)
    logging.info('===> Current Working Dir: {}'.format(os.getcwd()))
    generate_404_html(options.dir)

    start_server(
        port=options.port,
        max_items=options.max_items
    )


if __name__ == '__main__':
    # sys.exit(main())
    main()
