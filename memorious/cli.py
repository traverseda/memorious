import click
import logging
import time
from tabulate import tabulate

from memorious import settings
from memorious.core import manager, init_memorious
from memorious.task_runner import TaskRunner

log = logging.getLogger(__name__)


@click.group()
@click.option('--debug/--no-debug', default=False,
              envvar='MEMORIOUS_DEBUG')
@click.option('--cache/--no-cache', default=True,
              envvar='MEMORIOUS_HTTP_CACHE')
@click.option('--incremental/--non-incremental', default=True,
              envvar='MEMORIOUS_INCREMENTAL')
def cli(debug, cache, incremental):
    """Crawler framework for documents and structured scrapers."""
    settings.HTTP_CACHE = cache
    settings.INCREMENTAL = incremental
    settings.DEBUG = debug
    if settings.DEBUG:
        logging.basicConfig(level=logging.DEBUG)
    init_memorious()


def get_crawler(name):
    crawler = manager.get(name)
    if crawler is None:
        msg = 'Crawler [%s] not found.' % name
        raise click.BadParameter(msg, param=crawler)
    return crawler


@cli.command()
@click.argument('crawler')
def run(crawler):
    """Run a specified crawler."""
    crawler = get_crawler(crawler)
    crawler.cleanup()
    crawler.run()
    crawler.cleanup()


@cli.command()
@click.argument('crawler')
def flush(crawler):
    """Delete all data generated by a crawler."""
    crawler = get_crawler(crawler)
    crawler.flush()


@cli.command()
def process():
    """Start the queue and process tasks as they come. Blocks while waiting"""
    TaskRunner.run()


@cli.command()
def beat():
    """Loop and try to run scheduled crawlers at short intervals"""
    while True:
        manager.run_scheduled()
        time.sleep(settings.BEAT_INTERVAL)


@cli.command()
def list():
    """List the available crawlers."""
    crawler_list = []
    for crawler in manager:
        is_due = 'yes' if crawler.check_due() else 'no'
        if crawler.disabled:
            is_due = 'off'
        crawler_list.append([crawler.name,
                             crawler.description,
                             crawler.schedule,
                             is_due])
    headers = ['Name', 'Description', 'Schedule', 'Due']
    print(tabulate(crawler_list, headers=headers))


@cli.command()
def cleanup():
    """Run clean up all crawlers."""
    manager.run_cleanup()


@cli.command()
def scheduled():
    """Run crawlers that are due."""
    manager.run_scheduled()


def main():
    cli(obj={})


if __name__ == '__main__':
    main()
