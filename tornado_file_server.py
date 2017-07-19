#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Starts a Tornado static file/folder  server in a given directory.
To start the server in the current directory:
    tornado-file-server .
Then go to http://localhost:8888 to browse the directory.
Use the --prefix option to add a prefix to the served URL,
for example to match GitHub Pages' URL scheme:
    tornado-file-server . --prefix=jiffyclub
Then go to http://localhost:8888/jiffyclub/ to browse.
Use the --port option to change the port on which the server listens.
"""

from __future__ import print_function

import os
import sys
import time
import os.path as osp

from argparse import ArgumentParser

from tornado.routing import Router, Rule, Matcher, RuleRouter, PathMatches
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
import tornado.web


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

        return url_path


response_header = \
    '''
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
        sz = float(osp.getsize(path))

        unit_idx = 0
        while (sz > 1024):
            sz = sz / 1024
            unit_idx += 1

        sz_str = '%.3f %s' % (sz, sz_unit[unit_idx])

        return sz_str

    def get(self, path):
        request_path = self.request.path
        full_url = self.request.full_url()
        work_dir = os.getcwd() + request_path
        #print("===>FolderHandler.request_path: {}".format(request_path))
        #print("===>FolderHandler.full_url: {}".format(full_url))
        #print("===>FolderHandler.work_dir: {}".format(work_dir))

        if not self.request.path or self.request.path == '/':
            parent_url = full_url
        else:
            if full_url.endswith('/'):
                parent_url = osp.dirname(full_url[:-1])
            else:
                parent_url = osp.dirname(full_url)

        dir_list = os.listdir(work_dir)

        # os.listdir() returns a list in arbitray order on Linux filesystem
        if sys.platform is not 'win32':
            dir_list = sorted(dir_list, key=lambda s: s.lower())

        content = '<h1>Directory: {}</h1>'.format(request_path)
        content += '<h4><a href="{}">Go to Parent Dir</a></h4>'.format(
            parent_url)
        #content += '<h2>---------------------</h2>'
        num = len(dir_list)
        if num < 1:
            content += '<h4>Nothing under this directory</h4>'
            # print(content)
        else:
            #print("===>Found {} files/folders".format(num))
            content_table = \
                '''<table style="width:100%;text-align: left">
  <tr>
    <th>Name</th>
    <th>Type</th>
    <th>Modified Time</th>
    <th>File Size</th>
  </tr>
'''
            i = 0
            for item in dir_list:
                item_template = \
                    '''
  <tr>
    <td><a href="{}">{}</a></td>
    <td>{}</td>
    <td>{}</td>
    <td>{}</td>
  </tr>
'''

                #print('\n--->item {}'.format(i))
                #print('name: {}'.format(item))
                local_path = osp.join(work_dir, item)
                #print('local path: {}'.format(local_path))
                if osp.isdir(local_path):
                    i += 1

                modify_time = self.get_file_mtime(local_path)
                #print('modify time: {}'.format(modify_time))
                file_type = self.get_file_type(local_path)
                #print('file type: {}'.format(file_type))
                file_size = self.get_file_size(local_path)
                #print('file size: {}'.format(file_size))

                item_url = osp.join(full_url, item)
                #print('link url: {}'.format(item_url))
                #item_url = self.reverse_url(item)
                content_table += item_template.format(item_url, item,
                                                      file_type,
                                                      modify_time,
                                                      file_size
                                                      )

            content += "<h4>{} files, {} folders</h4>".format(num - i, i)
            content += content_table

        self.write(response_header + content)


class File_matcher(Matcher):
    def match(self, request):
        work_dir = os.getcwd() + request.path
        if osp.isfile(work_dir):
            return {}
        else:
            return None


class Folder_matcher(Matcher):
    def match(self, request):
        work_dir = os.getcwd() + request.path
        if osp.isdir(work_dir):
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
    #print("args: {}".format(args))
    os.chdir(args.dir)
    generate_404_html(args.dir)
    #print('Starting server on port {}'.format(args.port))
    start_server(prefix=args.prefix, port=args.port)


if __name__ == '__main__':
    sys.exit(main())
