#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
author: zhaoyafei0210@gmail.com
github: https://github.com/walkoncross/tornado-file-server

a tornado-based file server 
"""

from __future__ import print_function

import os.path as osp
import time
import os
import logging
import sys
import math


# from tornado.options import define, options
import tornado.options
import tornado.escape
import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.routing


from .get_ip import get_ip
from .python_version import is_python3


if is_python3():
    from builtins import str as unicode
    from urllib.parse import unquote
else:
    from urllib import unquote


content_404_html = u'''
<!DOCTYPE html>
<html>
  <body>
    <h1>404 - File or Directory Not Found.</h1>
  </body>
</html>
'''


def generate_404_html(save_dir):
    fp = open(osp.join(save_dir, '404.html'), 'w')
    fp.writelines(content_404_html)
    fp.close()


def get_full_local_path_for_url(uri_path, root_dir=None):
    if not root_dir:
        root_dir = unicode(os.getcwd())

    if not isinstance(root_dir, unicode):
        raise(AssertionError(
            "In get_full_local_path_for_url: root_dir must be Unicode"))

    if uri_path == '/':
        full_local_path = root_dir
    else:
        local_path = tornado.escape.url_unescape(uri_path, plus=True)
        # print('type(local_path): ', type(local_path))
        # print(local_path)
        # full_local_path = osp.join(root_dir, local_path) # Error: osp.join('/working/path/', '/static_file') = /static_file
        full_local_path = root_dir + local_path

    return full_local_path


class TypeMatchesFile(tornado.routing.Matcher):

    def __init__(self, root_dir=None):
        super(TypeMatchesFile, self).__init__()
        self.root_dir = root_dir

    def match(self, request):
        full_local_path = get_full_local_path_for_url(
            request.path, self.root_dir)

        # logging.info(u'full_local_path in TypeMatchesFile:', full_local_path)
        if osp.isfile(full_local_path):
            # print('--> request to access a local file')
            return {}
        else:
            return None


class TypeMatchesFolder(tornado.routing.Matcher):

    def __init__(self, root_dir=None):
        super(TypeMatchesFolder, self).__init__()
        self.root_dir = root_dir

    def match(self, request):
        full_local_path = get_full_local_path_for_url(
            request.path, self.root_dir)

        # logging.info(
        #     u'full_local_path in TypeMatchesFolder:{}'.format(full_local_path))
        if osp.isdir(full_local_path):
            # print('--> request to access a local folder')
            return {}
        else:
            return None


class FileHandler(tornado.web.StaticFileHandler):
    '''
    Static File Handler
    '''

    def parse_url_path(self, url_path):
        # logging.info(u'===> self.request.uri: {}'.format(self.request.uri))
        # logging.info(u'===> self.request.path: {}'.format(self.request.path))
        # logging.info(u'===> self.request.query: {}'.format(self.request.query))
        # logging.info(u'===> self.request.headers: {}'.format(self.request.headers))
        # logging.info(u'===> self.request.body: {}'.format(self.request.body))

        logging.info(
            u'GET file path: {}'.format(url_path)
        )

        if not url_path or url_path.endswith('/'):
            logging.info(
                u'Cannot find: {}'.format(url_path)
            )
            url_path = osp.join(self.root, '404.html')
            logging.info(
                u'Return: {}'.format(url_path)
            )

        if os.path.sep != "/":
            url_path = url_path.replace("/", os.path.sep)

        return url_path


class FolderHandler(tornado.web.RequestHandler):
    '''
    Request Handler to list a files under a directory
    '''

    response_header = u'''
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

    response_content_header_template = u'''
    <header>
    <h1>Directory: {}</h1>
    </header>
    '''

    response_content_navi_parent_template = u'''
    <nav>
    <h4><a href="{}">Go to Parent Dir</a></h4>
    </nav>   
    '''

    response_content_navi_prev_nohref = u'''
    &lt;Prev
    '''

    response_content_navi_next_nohref = u'''
    Next&gt;
    '''

    response_content_navi_prev_template = u'''
    <a href="{}">&lt;Prev</a> 
    '''

    response_content_navi_up_template = u'''
     <a href="{}">Up</a> 
    '''

    response_content_navi_next_template = u'''
     <a href="{}">Next&gt;</a>
    '''

    response_content_upload_form = u'''
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

    response_content_nothing_found = u'''
    <h4>Nothing under this directory</h4>
    '''

    response_content_table_summary_template = u'''
    <h4>{} items in total, {} files, {} folders</h4>
    <h4>show {} items per page, {} pages</h4>
    '''

    response_content_table_header = u'''
    <table style="width:100%;text-align: left">
    <tr>
    <th>Name</th>
    <th>Type</th>
    <th>Modified Time</th>
    <th>File Size</th>
    </tr>
    '''

    response_content_table_item_template = u'''
    <tr>
        <td><a href="{}">{}</a></td>
        <td>{}</td>
        <td>{}</td>
        <td>{}</td>
    </tr>
    '''

    response_content_table_footer = u'''
    </table>
    '''

    response_content_footer = u'''
    <footer>
    <p><a href="https://github.com/walkoncross/tornado-file-server">github repo</a></p>
    </footer>
    '''

    upload_response_content_header = u'''
    <p><a href={}>Back</a></p>
    <h4>OK</h4>
    '''

    upload_response_content_item_template = u'''
    <p><em>{}</em> saved into: <em>{}</em></p>
    '''

    def initialize(self, max_items_per_page=50, root_dir=None):
        '''initialize
        Refer to https://www.tornadoweb.org/en/stable/web.html:

        classtornado.web.RequestHandler(...)[source]
            Base class for HTTP request handlers.

            Subclasses must define at least one of the methods defined in the “Entry points” section below.

            Applications should not construct RequestHandler objects directly and subclasses should not override __init__ (override initialize instead).
        '''
        self.last_request_uri_path = ''
        self.uri_path = '/'
        self.parent_uri_path = '/'

        if not root_dir:
            self.root_dir = os.getcwd()
        else:
            self.root_dir = osp.abspath(root_dir)

        self.last_folder_mtime = ''
        self.dir_list = []
        self.dir_item_info_list = []

        self.dir_list_len = 0
        self.sub_folder_cnt = 0

        self.max_page_id = 1
        self.max_items_per_page = max_items_per_page

        self.update_dir_item_info_list()

    def get_file_mtime(self, path):
        mt = time.localtime(osp.getmtime(path))
        tm_str = time.strftime('%y-%m-%d %H:%M:%S', mt)

        return unicode(tm_str)

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

        return unicode(ftype)

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

        return unicode(sz_str)

    def update_dir_item_info_list(self):
        # unquote quoted self.request.path into local path
        # e.g. "%20" into " "
        self.uri_path = self.request.path

        unquoted_uri_path = tornado.escape.url_unescape(self.request.path)

        logging.info(
            u'===> Update folder dir_info: {}'.format(unquoted_uri_path)
        )
        # print('===> Update folder dir_info: {}'.format(unquoted_uri_path))
        # print('type(unquoted_uri_path: {}'.format(type(self.request.path)))

        if not self.request.path or self.request.path == '/':
            self.parent_uri_path = self.uri_path
        else:
            if self.request.path.endswith('/'):
                self.parent_uri_path = osp.dirname(self.request.path[:-1])
            else:
                self.parent_uri_path = osp.dirname(self.request.path)

        # use unicode to deal with Chinese characters
        full_local_path = get_full_local_path_for_url(
            self.uri_path, self.root_dir)
        #logging.info("===>full_local_path: {}".format(full_local_path))
        # print('--> full_local_path: ', full_local_path)

        self.last_folder_mtime = self.get_file_mtime(full_local_path)

        self.dir_list = os.listdir(full_local_path)
        # os.listdir() returns a list in arbitray order on Linux filesystem

        if sys.platform != 'win32':
            self.dir_list = sorted(self.dir_list, key=lambda s: s.lower())

        self.dir_list_len = len(self.dir_list)
        self.dir_item_info_list = []
        self.max_page_id = 1
        # self.last_request_uri_path = self.request.path
        self.sub_folder_cnt = 0

        if self.dir_list_len > 0:
            #logging.info("===>Found {} files/folders".format(self.dir_list_len))
            self.max_page_id = int(math.ceil(
                self.dir_list_len / float(self.max_items_per_page)))

            for item in self.dir_list:
                # print('--> type(item): ', type(item))
                # print(item)
                if not isinstance(item, unicode):
                    raise(AssertionError(
                        "File name must can be encoded into Unicode"))

                item_name_utf = item

                # if not is_python3():
                #     item_name_utf = item.decode('utf-8') # convert to unicode

                # print('--> type(item_name_utf): ', type(item_name_utf))
                # print(item_name_utf)

                item_full_path = osp.join(full_local_path, item_name_utf)
                # logging.info(u'item local path:', item_full_path)
                if osp.isdir(item_full_path):
                    self.sub_folder_cnt += 1

                modify_time = self.get_file_mtime(item_full_path)
                #logging.info(u'modify time: {}'.format(modify_time))
                file_type = self.get_file_type(item_full_path)
                #logging.info(u'file type: {}'.format(file_type))
                file_size = self.get_file_size(item_full_path)
                #logging.info(u'file size: {}'.format(file_size))

                # item_name_utf = item
                # item_name_utf = tornado.escape.to_unicode(item)

                # print('--> type(item_name_utf): ', type(item_name_utf))
                # print(item_name_utf)

                # print('--> type(self.request.path): ', type(self.request.path))

                item_uri_path = tornado.escape.url_escape(
                    item_name_utf, plus=True)
                # print('--> type(item_uri_path): ', type(item_uri_path))
                # print(item_uri_path)
                # item_uri_path = item

                item_uri_path = osp.join(self.request.path, item_uri_path)

                if file_type == 'DIR':
                    item_uri_path += '/'

                # print('--> type(item_uri_path): ', type(item_uri_path))
                # print(item_uri_path)

                # logging.info(u'===> link url: {}'.format(item_uri_path))
                #item_uri_path = self.reverse_url(item)

                self.dir_item_info_list.append(
                    (item_uri_path, item_name_utf,
                     modify_time, file_type, file_size)
                )

    def get(self, path):
        # logging.info(u'===> self.path_args: {}'.format(self.path_args))
        # logging.info(u'===> self.path_kwargs: {}'.format(self.path_kwargs))

        # logging.info(u'===> self.request.uri: {}'.format(self.request.uri))
        # logging.info(u'===> self.request.path: {}'.format(self.request.path))
        # logging.info(u'===> self.request.query: {}'.format(self.request.query))
        # logging.info(u'===> self.request.headers: {}'.format(self.request.headers))
        # logging.info(u'===> self.request.body: {}'.format(self.request.body))

        # if path == '':
        #     path = '/'

        logging.info(
            u'GET folder uri: {}'.format(self.request.uri)
        )

        if self.request.path != self.last_request_uri_path:
            logging.info(
                u'===> Last request uri path: {}'.format(
                    self.last_request_uri_path)
            )
            self.update_dir_item_info_list()
        else:
            full_local_path = get_full_local_path_for_url(
                self.request.path, self.root_dir)
            mtime = self.get_file_mtime(full_local_path)

            if mtime != self.last_folder_mtime:
                self.update_dir_item_info_list()

        page_id = self.get_query_argument(name="page_id", default='1')

        logging.info(
            u'page_id: {}'.format(page_id)
        )

        try:
            page_id = int(page_id)
        except:
            page_id = 1

        logging.info(
            u'max_page_id: {}'.format(self.max_page_id)
        )

        if page_id > self.max_page_id:
            page_id = 1

        logging.info(
            u'page_id after check: {}'.format(page_id)
        )

        response_content = FolderHandler.response_content_header_template.format(
            tornado.escape.url_unescape(self.uri_path))
        response_content += FolderHandler.response_content_navi_parent_template.format(
            self.parent_uri_path)
        response_content += FolderHandler.response_content_upload_form

        if self.dir_list_len < 1:
            response_content += FolderHandler.response_content_nothing_found
            # logging.info(response_content)
        else:
            response_content += FolderHandler.response_content_table_summary_template.format(
                self.dir_list_len,
                self.dir_list_len - self.sub_folder_cnt,
                self. sub_folder_cnt,
                self.max_items_per_page,
                self.max_page_id
            )

            content_navi = u''
            prev_page_id = page_id-1
            if prev_page_id < 1:
                content_navi += FolderHandler.response_content_navi_prev_nohref
            else:
                content_navi += FolderHandler.response_content_navi_prev_template.format(
                    self.request.path+'?page_id='+str(prev_page_id))

            content_navi += FolderHandler.response_content_navi_up_template.format(
                self.parent_uri_path)

            next_page_id = page_id+1
            if next_page_id > self.max_page_id:
                content_navi += FolderHandler.response_content_navi_next_nohref
            else:
                content_navi += FolderHandler.response_content_navi_next_template.format(
                    self.request.path+'?page_id='+str(next_page_id))

            response_content += content_navi
            #logging.info(u"===>Found {} files/folders".format(self.dir_list_len))
            FolderHandler.response_content_table = FolderHandler.response_content_table_header

            start_idx = self.max_items_per_page * (page_id-1)
            end_idx = min(self.max_items_per_page * page_id, self.dir_list_len)

            for i in range(start_idx, end_idx):
                item_info = self.dir_item_info_list[i]
                # logging.info(
                #     u'item_info: {}'.format(item_info)
                # )

                # for ii,info in enumerate(item_info):
                #     print('item_info[{}]: ', ii)
                #     print('type:', type(info))
                #     print(info)

                FolderHandler.response_content_table += FolderHandler.response_content_table_item_template.format(
                    # unicode(item_info[0]),
                    # unicode(item_info[1]),
                    # unicode(item_info[2]),
                    # unicode(item_info[3]),
                    # unicode(item_info[4])
                    item_info[0],
                    item_info[1],
                    item_info[2],
                    item_info[3],
                    item_info[4]
                )

            FolderHandler.response_content_table += FolderHandler.response_content_table_footer
            response_content += FolderHandler.response_content_table

            # response_content += FolderHandler.response_content_upload_form
            if end_idx - start_idx >= 10:
                response_content += content_navi

        response_content += FolderHandler.response_content_footer

        self.last_request_uri_path = self.request.path

        self.write(FolderHandler.response_header + response_content)

    def post(self, path):
        # logging.info(u'===> self.path_args: {}'.format(self.path_args))
        # logging.info(u'===> self.path_kwargs: {}'.format(self.path_kwargs))

        # logging.info(u'===> self.request.uri: {}'.format(self.request.uri))
        # logging.info(u'===> self.request.path: {}'.format(self.request.path))
        # logging.info(u'===> self.request.query: {}'.format(self.request.query))
        # logging.info(u'===> self.request.headers: {}'.format(self.request.headers))
        # logging.info(u'===> self.request.body: {}'.format(self.request.body))
        logging.info(
            'POST : {}'.format(self.request.uri)
        )

        # print('path: ', path)

        response_content = FolderHandler.upload_response_content_header.format(
            self.request.path)
        full_local_path = get_full_local_path_for_url(
            self.request.path, self.root_dir)

        for field_name, files in self.request.files.items():
            for info in files:
                filename, content_type = info["filename"], info["content_type"]

                if not is_python3():
                    filename = filename.decode('utf-8')

                body = info["body"]
                logging.info(
                    'POST "%s" "%s" %d bytes', filename, content_type, len(
                        body)
                )

                save_filename = osp.join(
                    full_local_path, osp.basename(filename))
                if osp.isfile(save_filename):
                    i = 0
                    fn, ext = osp.splitext(save_filename)

                    while osp.isfile(save_filename):
                        i += 1
                        save_filename = fn + '.{:03d}'.format(i) + ext

                fp = open(save_filename, 'wb')
                fp.write(body)
                fp.close()

                response_content += FolderHandler.upload_response_content_item_template.format(
                    filename, save_filename)

        self.write(response_content)


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
#         logging.info(u'PUT "%s" "%s" %d bytes',
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
# def start_server(prefix='', port=8899):
#    app = mkapp(prefix)
#    app.listen(port)
#    tornado.ioloop.IOLoop.instance().start()


def start_server(root_dir, port=8899, max_items=50):
    if not isinstance(root_dir, unicode):
        raise(AssertionError("In start_server: root_dir must be of type Unicode"))

    ip = get_ip()
    server_url = u"{}:{}".format(ip, port)
    print('===> tornado file server url: \n', server_url)

    logging.info(
        u'===> tornado file server url: {} or localhost:{}'.format(server_url, port)
    )

    path = '/(.*)'

    file_app = tornado.web.Application(
        [
            (path, FileHandler, {'path': root_dir}),
        ],
        debug=True
    )

    folder_app = tornado.web.Application(
        [
            (path, FolderHandler, {
             "max_items_per_page": max_items, "root_dir": root_dir}),
        ],
        debug=True
    )

    error_app = tornado.web.Application(
        [
            (path, tornado.web.ErrorHandler, {"status_code": 404}),
        ],
        debug=True
    )
    # post_app = tornado.web.Application(
    #     [
    #         (r"/post", POSTHandler),
    #         # (r"/(.*)", PUTHandler)
    #     ]
    # )

    router = tornado.routing.RuleRouter(
        [
            tornado.routing.Rule(TypeMatchesFile(root_dir=root_dir), file_app),
            tornado.routing.Rule(TypeMatchesFolder(
                root_dir=root_dir), folder_app),
            tornado.routing.Rule(tornado.routing.AnyMatches(), error_app),
            # tornado.routing.Rule(tornado.routing.PathMatches(r"/post"), post_app)
            # tornado.routing.Rule(tornado.routing.PathMatches(path + r"/post"), post_app)
        ]
    )

#    router = tornado.routing.RuleRouter(
#       [
#           tornado.routing.Rule(tornado.routing.PathMatches("/app1.*"), file_app),
#           tornado.routing.Rule(tornado.routing.PathMatches("/app2.*"), folder_app)
#       ]
#    )

    server = tornado.httpserver.HTTPServer(router)
    server.listen(port)
    tornado.ioloop.IOLoop.current().start()
