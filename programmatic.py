import krauler


@krauler.on_wait.connect
def make_session(krauler):
    krauler.crawl('http://pudo.org')


if __name__ == '__main__':
    krauler.crawl_to_metafolder({
        'path': '$HOME/tmp/kraul',
        'crawl': {
            'domains': ['pudo.org'],
            'domains_deny': ['data.pudo.org', 'usual-suppliers.pudo.org']
        }
    })
