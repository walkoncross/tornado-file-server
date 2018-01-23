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

import os
import sys
import time
import os.path as osp

from argparse import ArgumentParser

from tornado.routing import Rule, Matcher, RuleRouter, PathMatches
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
import tornado.web

from tornado.escape import url_escape, url_unescape


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


class FileHandler(tornado.web.StaticFileHandler):
    '''
    Static File Handler
    '''

    def parse_url_path(self, url_path):
        #print("FileHandler.root: {}".format(self.root))
        #print("FileHandler.url_path: {}".format(url_path))
        #print("FileHandler.request.path: {}".format(self.request.path))
        ##print("self.request: {}".format(self.request))

        if not url_path or url_path.endswith('/'):
            url_path = osp.join(self.root, '404.html')

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
        # print('type(self.request.uri): ', type(self.request.uri))
        # print('===> self.request.uri: ', self.request.uri)
        # print('===> self.request.path: ', self.request.path)

        # unquote quoted self.request.path into local path
        # e.g. "%20" into " "
        local_path = url_unescape(self.request.path, plus=False)
        # print('===> type(local_path): ', type(local_path))
        # print('===> local local_path: ', local_path)
        full_url = self.request.full_url()

        # use unicode to deal with Chinese characters
        full_local_path = unicode(os.getcwd()) + local_path
        #print("===>FolderHandler.local_path: {}".format(local_path))
        #print("===>FolderHandler.full_url: {}".format(full_url))
        #print("===>FolderHandler.full_local_path: {}".format(full_local_path))

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

        content = '<h1>Directory: {}</h1>'.format(local_path)
        content += '<h4><a href="{}">Go to Parent Dir</a></h4>'.format(
            parent_url)
        #content += '<h2>---------------------</h2>'
        num = len(dir_list)
        if num < 1:
            content += '<h4>Nothing under this directory</h4>'
            # print(content)
        else:
            #print("===>Found {} files/folders".format(num))
            content_table = content_table_header

            sub_folder_cnt = 0
            for i, item in enumerate(dir_list):
                # print('\n--->item {}'.format(i))
                # print('type(item): ', type(item))
                # print(u'name:', item)
                item_local_path = osp.join(full_local_path, item)
                # print(u'item local path:', item_local_path)
                if osp.isdir(item_local_path):
                    sub_folder_cnt += 1

                modify_time = self.get_file_mtime(item_local_path)
                #print('modify time: {}'.format(modify_time))
                file_type = self.get_file_type(item_local_path)
                #print('file type: {}'.format(file_type))
                file_size = self.get_file_size(item_local_path)
                #print('file size: {}'.format(file_size))

                item_utf = item.encode('utf-8')

                item_url = url_escape(item_utf, plus=False)
                item_url = osp.join(full_url, item_utf)
                # print('===> link url: {}'.format(item_url))
                #item_url = self.reverse_url(item)
                content_table += content_table_item_template.format(item_url, item_utf,
                                                                    file_type,
                                                                    modify_time,
                                                                    file_size
                                                                    )

            content += "<h4>{} files, {} folders</h4>".format(
                num - sub_folder_cnt, sub_folder_cnt)
            content_table += content_table_footer
            content += content_table

        self.write(response_header + content)


class File_matcher(Matcher):
    def match(self, request):
        full_local_path = unicode(
            os.getcwd()) + url_unescape(request.path, plus=False)
        # print(u'full_local_path in File_matcher:', full_local_path)
        if osp.isfile(full_local_path):
            return {}
        else:
            return None


class Folder_matcher(Matcher):
    def match(self, request):
        full_local_path = unicode(
            os.getcwd()) + url_unescape(request.path, plus=False)
        # print(u'full_local_path in Folder_matcher:', full_local_path)
        if osp.isdir(full_local_path):
            return {}
        else:
            return None


# def mkapp(prefix=''):
#    if prefix:
#        path = '/' + prefix + '/(.*)'
#    else:
#        path = '/(.*)'
#
#    #print("os.getcwd() = : {}".format(os.getcwd()))
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

    file_app = tornado.web.Application([
        (path, FileHandler, {'path': os.getcwd()}),
    ], debug=True)

    folder_app = tornado.web.Application([
        (path, FolderHandler),
    ], debug=True)

    router = RuleRouter([
        Rule(File_matcher(), file_app),
        Rule(Folder_matcher(), folder_app)
    ])

#    router = RuleRouter([
#        Rule(PathMatches("/app1.*"), file_app),
#        Rule(PathMatches("/app2.*"), folder_app)
#    ])

    server = HTTPServer(router)
    server.listen(port)
    IOLoop.current().start()


def generate_404_html(save_dir):
    content = \
        '''<!DOCTYPE html>
<html>
<body>
<h1>404 - File or Directory Not Found.</h1>
</body>
</html>
'''
    fp = open(osp.join(save_dir, '404.html'), 'w')
    fp.writelines(content)
    fp.close()


def main(args=None):
    args = parse_args(args)
    print("args: {}".format(args))
    os.chdir(args.dir)
    print('===> Current Working Dir: ', os.getcwd())
    generate_404_html(args.dir)
    #print('Starting server on port {}'.format(args.port))
    start_server(prefix=args.prefix, port=args.port)


if __name__ == '__main__':
    sys.exit(main())
