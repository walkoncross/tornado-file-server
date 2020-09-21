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

from argparse import ArgumentParser

from tornado.routing import Rule, Matcher, RuleRouter, PathMatches
from tornado.httpserver import HTTPServer
import tornado.ioloop
# from tornado.ioloop import IOLoop
import tornado.web
from tornado import options

from tornado.escape import url_escape, url_unescape

# if sys.version.startswith('3.'):
#     from builtins import str as unicode


# save_dir = './uploaded_files'
# if not osp.isdir(save_dir):
#     os.makedirs(save_dir)

logging.basicConfig()

def parse_args(args=None):
    parser = ArgumentParser(
        description=(
            'Start a Tornado server to serve static files and folders out of a '
            'given directory and with a given prefix.'))
    parser.add_argument(
        '-f', '--prefix', type=str, default='',
        help='A prefix to add to the location from which pages are served.')
    parser.add_argument(
        '-p', '--port', type=int, default=8888,
        help='Port on which to run server.')
    parser.add_argument(
        'dir', help='Directory from which to serve files.')
    return parser.parse_args(args)


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
        #logging.info("FileHandler.root: {}".format(self.root))
        #logging.info("FileHandler.url_path: {}".format(url_path))
        #logging.info("FileHandler.request.path: {}".format(self.request.path))
        ##logging.info("self.request: {}".format(self.request))
        logging.info(
            'GET ', url_path
        )

        if not url_path or url_path.endswith('/'):
            logging.info(
                'Cannot find: ', url_path
            )
            url_path = osp.join(self.root, '404.html')
            logging.info(
                'Return: ', url_path
            )

        if os.path.sep != "/":
            url_path = url_path.replace("/", os.path.sep)

        return url_path


response_header = '''
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

content_navi_template = '''
<h1>Directory: {}</h1>
<h4><a href="{}">Go to Parent Dir</a></h4>
'''

content_upload_form = '''
<form method="post" enctype="multipart/form-data">
  <div>
    <label for="files">Choose files</label>
    <input type="file" id="files" name="files" multiple>
  </div>
  <div>
    <button>Upload</button>
  </div>
</form>
'''

content_table_header = '''
<table style="width:100%;text-align: left">
  <tr>
    <th>Name</th>
    <th>Type</th>
    <th>Modified Time</th>
    <th>File Size</th>
  </tr>
'''

content_table_item_template = '''
  <tr>
    <td><a href="{}">{}</a></td>
    <td>{}</td>
    <td>{}</td>
    <td>{}</td>
  </tr>
'''

content_table_summary_template = '''
<h4>{} files, {} folders</h4>
'''

content_table_footer = '''
</table>
'''


class FolderHandler(tornado.web.RequestHandler):
    '''
    Request Handler to list a files under a directory
    '''

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

    def get(self, path):
        # logging.info('type(self.request.uri): ', type(self.request.uri))
        # logging.info('===> self.request.uri: ', self.request.uri)
        # logging.info('===> self.request.path: ', self.request.path)
        logging.info(
            'GET ', path
        )

        # unquote quoted self.request.path into local path
        # e.g. "%20" into " "
        local_path = url_unescape(self.request.path, plus=False)
        # logging.info('===> type(local_path): ', type(local_path))
        # logging.info('===> local local_path: ', local_path)
        full_url = self.request.full_url()

        # use unicode to deal with Chinese characters
        full_local_path = unicode(os.getcwd()) + local_path
        #logging.info("===>FolderHandler.local_path: {}".format(local_path))
        #logging.info("===>FolderHandler.full_url: {}".format(full_url))
        #logging.info("===>FolderHandler.full_local_path: {}".format(full_local_path))

        if not self.request.path or self.request.path == '/':
            parent_url = full_url
        else:
            if full_url.endswith('/'):
                parent_url = osp.dirname(full_url[:-1])
            else:
                parent_url = osp.dirname(full_url)

        dir_list = os.listdir(full_local_path)

        # os.listdir() returns a list in arbitray order on Linux filesystem
        if sys.platform is not 'win32':
            dir_list = sorted(dir_list, key=lambda s: s.lower())

        content = content_navi_template.format(local_path, parent_url)
        content += content_upload_form

        #content += '<h2>---------------------</h2>'
        num = len(dir_list)
        if num < 1:
            content += '<h4>Nothing under this directory</h4>'
            # logging.info(content)
        else:
            #logging.info("===>Found {} files/folders".format(num))
            content_table = content_table_header

            sub_folder_cnt = 0
            for i, item in enumerate(dir_list):
                # logging.info('\n--->item {}'.format(i))
                # logging.info('type(item): ', type(item))
                # logging.info(u'name:', item)
                item_local_path = osp.join(full_local_path, item)
                # logging.info(u'item local path:', item_local_path)
                if osp.isdir(item_local_path):
                    sub_folder_cnt += 1

                modify_time = self.get_file_mtime(item_local_path)
                #logging.info('modify time: {}'.format(modify_time))
                file_type = self.get_file_type(item_local_path)
                #logging.info('file type: {}'.format(file_type))
                file_size = self.get_file_size(item_local_path)
                #logging.info('file size: {}'.format(file_size))

                item_utf = item.encode('utf-8')

                item_url = url_escape(item_utf, plus=False)
                item_url = osp.join(full_url, item_utf)
                # logging.info('===> link url: {}'.format(item_url))
                #item_url = self.reverse_url(item)
                content_table += content_table_item_template.format(item_url, item_utf,
                                                                    file_type,
                                                                    modify_time,
                                                                    file_size
                                                                    )

            content += content_table_summary_template.format(
                num - sub_folder_cnt, sub_folder_cnt)
            content_table += content_table_footer
            content += content_table

        self.write(response_header + content)

    def post(self, path):
        response_content = "<h4>OK</h4>\n"

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

                response_content += "<p><em>{}</em> saved into: <em>{}</em></p>\n".format(
                    filename, save_filename)

        self.write(response_content)


class File_matcher(Matcher):
    def match(self, request):
        full_local_path = unicode(
            os.getcwd()) + url_unescape(request.path, plus=False)
        # logging.info(u'full_local_path in File_matcher:', full_local_path)
        if osp.isfile(full_local_path):
            return {}
        else:
            return None


class Folder_matcher(Matcher):
    def match(self, request):
        full_local_path = unicode(
            os.getcwd()) + url_unescape(request.path, plus=False)
        # logging.info(u'full_local_path in Folder_matcher:', full_local_path)
        if osp.isdir(full_local_path):
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


def start_server(prefix='', port=8888):
    if prefix:
        path = '/' + prefix + '/(.*)'
    else:
        path = '/(.*)'

    file_app = tornado.web.Application(
        [
            (path, FileHandler, {'path': os.getcwd()}),
        ],
        debug=True
    )

    folder_app = tornado.web.Application(
        [
            (path, FolderHandler),
        ],
        debug=True)

    # post_app = tornado.web.Application(
    #     [
    #         (r"/post", POSTHandler),
    #         # (r"/(.*)", PUTHandler)
    #     ]
    # )

    router = RuleRouter([
        Rule(File_matcher(), file_app),
        Rule(Folder_matcher(), folder_app),
        # Rule(PathMatches(r"/post"), post_app)
        # Rule(PathMatches(path + r"/post"), post_app)
    ])

#    router = RuleRouter([
#        Rule(PathMatches("/app1.*"), file_app),
#        Rule(PathMatches("/app2.*"), folder_app)
#    ])

    server = HTTPServer(router)
    server.listen(port)
    tornado.ioloop.IOLoop.current().start()


def generate_404_html(save_dir):
    fp = open(osp.join(save_dir, '404.html'), 'w')
    fp.writelines(content_404_html)
    fp.close()


def main(args=None):
    args = parse_args(args)
    logging.info("===> args: {}".format(args))
    os.chdir(args.dir)
    logging.info('===> Current Working Dir: ', os.getcwd())
    generate_404_html(args.dir)
    #logging.info('Starting server on port {}'.format(args.port))
    start_server(prefix=args.prefix, port=args.port)


if __name__ == '__main__':
    # sys.exit(main())
    main()
