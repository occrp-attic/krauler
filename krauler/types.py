import mimetypes

from krauler.rules import Rule

mimetypes.add_type('.htm', 'text/html')
mimetypes.add_type('.asp', 'text/html')
mimetypes.add_type('.aspx', 'text/html')
mimetypes.add_type('.php', 'text/html')
mimetypes.add_type('.jsp', 'text/html')

GROUPS = {
    'web': ['text/html', 'text/plain'],
    'images': ['image/jpeg', 'image/bmp', 'image/png', 'image/tiff',
               'image/gif', 'application/postscript', 'image/vnd.dxf',
               'image/svg+xml', 'image/x-pict'],
    'documents': ['application/vnd.ms-excel', 'application/msword', 'application/pdf',
                  'application/vnd.ms-powerpoint', 'application/vnd.oasis.opendocument.text',
                  'application/vnd.oasis.opendocument.spreadsheet',
                  'application/rtf', 'application/x-rtf', 'text/richtext',
                  'application/vnd.oasis.opendocument.graphics',
                  'application/vnd.oasis.opendocument.presentation',
                  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                  'application/vnd.openxmlformats-officedocument.presentationml.presentation'],
    'archives': ['application/zip', 'application/x-rar-compressed', 'application/x-tar',
                 'application/x-gzip', 'application/x-7z-compressed'],
    'assets': ['text/css', 'application/javascript', 'application/json', 'image/x-icon',
               'application/rss+xml']
}


class MimeTypeRule(Rule):

    def apply(self, page):
        return self.page.mime_type == self.value


class MimeGroupRule(Rule):

    def apply(self, page):
        if page.mime_type.startswith('%s/' % self.value):
            return True
        return page.mime_type in GROUPS.get(self.value, [])
