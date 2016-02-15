#!/usr/bin/python
import yaml
import click
import logging
import requests

from krauler.mf import MetaFolderKrauler

requests.packages.urllib3.disable_warnings()

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('requests').setLevel(logging.WARNING)
# logging.getLogger('dataset').setLevel(logging.WARNING)


@click.command()
@click.argument('config', type=click.Path(exists=True))
@click.option('--path', type=click.Path(), default=None)
def main(config, path):
    with open(config, 'rb') as fh:
        config = yaml.load(fh)

    if path is not None:
        config['path'] = path

    # TODO: validate config format
    print config
    mfk = MetaFolderKrauler(config)
    mfk.run()


if __name__ == "__main__":
    main()
