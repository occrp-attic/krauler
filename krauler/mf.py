import os
import logging
from lxml import html
from dateutil.parser import parse
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

    def get_content(self, page, meta):
        if not page.is_html:
            return page.content

        for meta_el in ['title', 'author', 'date']:
            path = self.config.get('%s_path' % meta_el)
            if path is not None and page.doc.findtext(path):
                meta[meta_el] = page.doc.findtext(path)

        if 'date' in meta:
            try:
                date = meta.pop('date')
                date = parse(date)
                if 'dates' not in meta:
                    meta['dates'] = []
                meta['dates'].append(date.isoformat())
            except Exception as ex:
                log.exception(ex)

        body = page.doc
        if self.config.get('body_path') is not None:
            body = page.doc.find(self.config.get('body_path'))

        for path in self.config.get('remove_paths', []):
            for el in body.findall(path):
                el.drop_tree()

        return html.tostring(body)

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

        self.metafolder.add_data(self.get_content(page, meta),
                                 page.normalized_url,
                                 meta=meta)
