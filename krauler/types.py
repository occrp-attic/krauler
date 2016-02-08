import mimetypes
from urlparse import urlparse


mimetypes.add_type('.htm', 'text/html')
mimetypes.add_type('.asp', 'text/html')
mimetypes.add_type('.aspx', 'text/html')
mimetypes.add_type('.php', 'text/html')
mimetypes.add_type('.jsp', 'text/html')

WEB = ['text/html', 'text/plain']

IMAGE = ['image/jpeg', 'image/bmp', 'image/png', 'image/tiff', 'image/gif',
         'application/postscript', 'image/vnd.dxf', 'image/svg+xml',
         'image/x-pict']

# AUDIO_EXT = ['mp3', 'wma', 'ogg', 'wav', 'ra', 'aac', 'mid', 'au',
#              'aiff']

# VIDEO_EXT = ['3gp', 'asf', 'asx', 'avi', 'mov', 'mp4', 'mpg', 'qt',
#              'rm', 'swf', 'wmv', 'm4a']

DOCUMENTS = ['application/vnd.ms-excel', 'application/msword', 'application/pdf',
             'application/vnd.ms-powerpoint', 'application/vnd.oasis.opendocument.text',
             'application/vnd.oasis.opendocument.spreadsheet',
             'application/rtf', 'application/x-rtf', 'text/richtext',
             'application/vnd.oasis.opendocument.graphics',
             'application/vnd.oasis.opendocument.presentation',
             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
             'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
             'application/vnd.openxmlformats-officedocument.presentationml.presentation']

ARCHIVE = ['application/zip', 'application/x-rar-compressed', 'application/x-tar',
           'gzip', 'bzip2', 'application/x-7z-compressed']

# BIN_EXT = ['css', 'exe', 'bin', 'rss', 'app', 'dmg']

ASSETS = ['text/css', 'application/javascript', 'application/json', 'image/x-icon',
          'application/rss+xml']


TYPES = {
    'web': WEB,
    'images': IMAGE,
    # 'audio': AUDIO_EXT,
    # 'video': VIDEO_EXT,
    'documents': DOCUMENTS,
    'archives': ARCHIVE,
    # 'binaries': BIN_EXT,
    'assets': ASSETS
}


def normalize_types(type_names):
    types = []
    for type_name in type_names:
        if type_name in TYPES:
            types.extend(TYPES[type_name])
        else:
            types.append(type_name)

    norm_types = []
    for type_name in types:
        type_name = type_name.lower().strip('.')
        if '/' not in type_name:
            fake_path = '/index.%s' % type_name
            mime, clazz = mimetypes.guess_type(fake_path)
            type_name = mime or clazz or type_name
        norm_types.append(type_name)
    return norm_types


def url_type(url):
    parsed = urlparse(url)
    url_type, url_class = mimetypes.guess_type(parsed.path)
    url_type = url_type or url_class
    if url_type == 'application/octet-stream' or url_type is None:
        return None
    return url_type.lower().strip('.')
