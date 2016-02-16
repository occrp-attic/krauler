#!/usr/bin/python
import yaml
import click

from krauler.util import configure_logging
from krauler.mf import MetaFolderKrauler

configure_logging()


@click.command()
@click.argument('config', type=click.Path(exists=True))
@click.option('--path', type=click.Path(), default=None)
@click.option('--threads', '-t', type=int, default=None)
def main(config, path, threads):
    with open(config, 'rb') as fh:
        config = yaml.load(fh)

    if path is not None:
        config['path'] = path

    if threads is not None:
        config['threads'] = threads

    # TODO: validate config format
    mfk = MetaFolderKrauler(config)
    mfk.run()


if __name__ == "__main__":
    main()
