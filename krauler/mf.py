import os
import logging
from lxml import html
import metafolder

from krauler.state import Krauler
from krauler.signals import on_meta

log = logging.getLogger(__name__)


class MetaFolderKrauler(Krauler):

    @property
    def metafolder(self):
        if not hasattr(self, '_metafolder'):
            path = self.config.get('path', '.')
            path = os.path.expandvars(path)
            path = os.path.expanduser(path)
            path = os.path.abspath(path)
            log.info("Saving output to: %r", path)
            self._metafolder = metafolder.open(path)
        return self._metafolder

    @property
    def overwrite(self):
        return self.config.get('overwrite', False)

    def get_content(self, page):
        if not page.is_html:
            return page.content

        for path in self.config.get('remove_paths', []):
            for el in page.doc.findall(path):
                el.drop_tree()

        return html.tostring(page.doc)

    def emit(self, page):
        if not self.overwrite:
            if self.metafolder.get(page.normalized_url).exists:
                return

        meta = self.config.get('meta', {}).copy()
        meta['source_url'] = page.normalized_url
        meta['foreign_id'] = page.normalized_url
        if page.file_name:
            meta['file_name'] = page.file_name
        meta['mime_type'] = page.mime_type
        meta['headers'] = dict(page.response.headers)
        
        on_meta.send(self, page=page, meta=meta)

        self.metafolder.add_data(self.get_content(page),
                                 page.normalized_url,
                                 meta=meta)
