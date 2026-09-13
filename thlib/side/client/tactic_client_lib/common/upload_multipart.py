###########################################################
#
# Copyright (c) 2005, Southpaw Technology
#                     All Rights Reserved
#
#
#

__all__ = ['UploadMultipart', 'TacticUploadException']

import socket
import base64

try:
    import urlparse
except:
    from urllib import parse as urlparse

try:
    import httplib
except:
    from http import client as httplib


import os, sys

class TacticUploadException(Exception):
    pass

class UploadMultipart(object):
    '''Handles the multipart content type for uploading files.  Will break up
    a file into chunks and upload separately for huge files'''

    max_upload_attempts = 5

    def __init__(self):
        self.tries = 0
        self.chunk_size = 10*1024*1024
        self.ticket = None
        self.subdir = None

        self.server_url = None

        self.offset = 0


    def set_offset(self, offset):
        self.offset = offset


    def set_upload_server(self, server_url):
        self.server_url = server_url


    def set_chunk_size(self, size):
        '''set the chunk size of each upload'''
        self.chunk_size = size

    def set_ticket(self, ticket):
        '''set the ticket for security'''
        self.ticket = ticket

    def set_subdir(self, subdir):
        self.subdir = subdir


    def execute(self, path, progress_signal=None):
        assert self.server_url
        file_size = os.stat(path).st_size
        total_count = int(file_size / self.chunk_size)
        if total_count == 0:
            total_count = 1
        info_dict = {
            'status_text': 'Uploading to Server ...',
            'total_count': total_count
        }
        import thlib.global_functions as gf

        with open(path, 'rb') as source_file:
            if self.offset:
                source_file.seek(self.offset * self.chunk_size)
            else:
                self.offset = 0

            while True:
                buffer = source_file.read(self.chunk_size)
                if not buffer:
                    break

                action = "create" if self.offset == 0 else "append"
                fields = [
                    ("ajax", "true"),
                    ("action", action),
                ]
                if self.ticket:
                    fields.append(("ticket", self.ticket))
                    fields.append(("login_ticket", self.ticket))
                    basename = os.path.basename(path)
                    from json import dumps as jsondumps

                    # Maya's output stream may not expose an encoding.
                    try:
                        if (
                            getattr(sys.stdout, "encoding", None) is not None
                            and sys.stdout.encoding
                        ):
                            basename = basename.decode(sys.stdout.encoding)
                        else:
                            import locale
                            basename = basename.decode(
                                locale.getpreferredencoding()
                            )
                    except AttributeError:
                        # Python 3 file names are already strings.
                        pass

                    basename = jsondumps(basename).strip('"')
                    fields.append(("file_name0", basename))

                if self.subdir:
                    fields.append(("subdir", self.subdir))

                files = [("file", path, buffer)]
                status, reason, _content = self.upload(
                    self.server_url, fields, files
                )

                current_uploaded = self.offset * self.chunk_size
                info_dict['status_text'] = 'Uploading {1} of {0}'.format(
                    gf.sizes(file_size), gf.sizes(current_uploaded)
                )
                if self.offset == 0:
                    gf.emit_progress(1, info_dict, progress_signal)
                else:
                    gf.emit_progress(
                        self.offset, info_dict, progress_signal
                    )

                if reason != "OK":
                    raise TacticUploadException(
                        "Upload of '%s' failed: %s %s"
                        % (path, status, reason)
                    )

                self.offset += 1



    def upload(self, url, fields, files):
        last_error = None
        try:
            for attempt in range(1, self.max_upload_attempts + 1):
                self.tries = attempt
                try:
                    result = self.posturl(url, fields, files)
                    if not isinstance(result, tuple) or len(result) != 3:
                        raise TacticUploadException(
                            "The TACTIC upload server returned an invalid "
                            "response"
                        )
                    status, reason, content = result
                    if status != 200:
                        raise TacticUploadException(
                            "The TACTIC upload server returned HTTP "
                            "%s %s" % (status, reason)
                        )
                    return status, reason, content
                except (UnicodeError, TypeError, ValueError) as error:
                    raise TacticUploadException(
                        "TACTIC file upload could not prepare the request: %s"
                        % error
                    ) from error
                except Exception as error:
                    last_error = error
                    if attempt == self.max_upload_attempts:
                        break
            raise TacticUploadException(
                "TACTIC file upload failed after %s attempts: %s"
                % (self.max_upload_attempts, last_error)
            ) from last_error
        finally:
            self.tries = 0



    # Repurposed from:
    # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/146306

    def posturl(self, url, fields, files):
        #print("URL ", url)
        urlparts = urlparse.urlsplit(url)
        protocol = urlparts[0]
 
        return self.post_multipart(urlparts[1], urlparts[2], fields,files, protocol)
                


    def post_multipart(self, host, selector, fields, files, protocol):
        '''
        Post fields and files to an http host as multipart/form-data.
        fields is a sequence of (name, value) elements for regular form fields.
        files is a sequence of (name, filename, value) elements for data to be uploaded as files.dirk.noteboom@sympatico.ca
        '''
        content_type, body = self.encode_multipart_formdata(fields, files)
        if protocol == 'https':
            h = httplib.HTTPSConnection(host)  
        else:
            h = httplib.HTTPConnection(host)  
        headers = {
            'User-Agent': 'Tactic Client',
            'Content-Type': content_type
            }

        # prevent upgrading the method + url in the httplib module to turn it 
        # into a unicode string before sending the request
        selector = str(selector)
        h.request('POST', selector, body, headers)
        res = h.getresponse()
        return res.status, res.reason, res.read()    


    def encode_multipart_formdata(self, fields, files):
        '''
        fields is a sequence of (name, value) elements for regular form fields.
        files is a sequence of (name, filename, value) elements for data to be uploaded as files.
        Return (content_type, body) ready for httplib.HTTPConnection instance
        '''
        boundary = '----------ThIs_Is_tHe_bouNdaRY_---$---'
        lines = []

        for key, value in fields:
            lines.extend((
                '--' + boundary,
                'Content-Disposition: form-data; name="%s"' % key,
                '',
                str(value),
            ))
        for key, filename, value in files:
            filename = os.path.basename(str(filename))
            filename = filename.replace('\r', '').replace('\n', '')
            filename = filename.replace('"', '\\"')
            lines.extend((
                '--' + boundary,
                'Content-Disposition: form-data; name="%s"; '
                'filename="%s"' % (key, filename),
                '',
                # TACTIC UploadServer expects this base64 marker.
                'data:xyz/xyz;base64,',
                base64.b64encode(value).decode('ascii'),
            ))
        lines.extend(('--' + boundary + '--', ''))

        body = '\r\n'.join(lines).encode('utf-8')
        content_type = 'multipart/form-data; boundary=%s' % boundary
        return content_type, body 





