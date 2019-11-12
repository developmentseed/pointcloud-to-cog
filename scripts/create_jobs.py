"""create_job: Feed SQS queue."""

import json
from functools import partial
from concurrent import futures
from collections import Counter
from urllib.parse import urlparse

import click

from boto3.session import Session as boto3_session

from rasterio.rio import options
from rio_tiler.utils import _chunks
from rio_cogeo.profiles import cog_profiles


def sources_callback(ctx, param, value):
    """
    Validate scheme and uniqueness of sources.

    From: https://github.com/mapbox/pxm-manifest-specification/blob/master/manifest.py#L157-L179

    Notes
    -----
    The callback takes a fileobj, but then converts it to a sequence
    of strings.

    Returns
    -------
    list

    """
    sources = list([name.strip() for name in value])

    # Validate scheme.
    schemes = [urlparse(name.strip()).scheme for name in sources]
    invalid_schemes = [
        scheme for scheme in schemes if scheme not in ["s3", "http", "https"]
    ]
    if len(invalid_schemes):
        raise click.BadParameter(
            "Schemes {!r} are not valid and should be on of 's3/http/https'.".format(
                invalid_schemes
            )
        )

    # Identify duplicate sources.
    dupes = [name for (name, count) in Counter(sources).items() if count > 1]
    if len(dupes) > 0:
        raise click.BadParameter(
            "Duplicated sources {!r} cannot be processed.".format(dupes)
        )

    return sources


def aws_send_message(message, topic, client=None):
    """Send SNS message."""
    if not client:
        session = boto3_session()
        client = session.client('sns')
    return client.publish(Message=json.dumps(message), TargetArn=topic)


def sns_worker(messages, topic, subject=None):
    """Send batch of SNS messages."""
    session = boto3_session()
    client = session.client('sns')
    for message in messages:
        aws_send_message(message, topic, client=client)
    return True


@click.command()
@click.argument("sources", default="-", type=click.File("r"), callback=sources_callback)
@click.option(
    "--cog-profile",
    "-p",
    "cogeo_profile",
    type=click.Choice(cog_profiles.keys()),
    default="deflate",
    help="CloudOptimized GeoTIFF profile (default: deflate).",
)
@options.creation_options
@click.option(
    "--options",
    "--op",
    "options",
    metavar="NAME=VALUE",
    multiple=True,
    callback=options._cb_key_val,
    help="rio_cogeo.cogeo.cog_translate input options.",
)
@click.option(
    "--prefix",
    type=str,
    default="cogs",
    help="AWS S3 Key prefix."
)
@click.option(
    "--topic",
    type=str,
    required=True,
    help="SNS Topic",
)
@click.option(
    "--resolution",
    type=float,
    default=0.25,
    help="Length of raster cell edges in X/Y units. (default: 0.25)",
)
@click.option(
    "--layers",
    type=str,
    default="min,max",
    help="A comma separated list of statistics for which to produce raster layers. (default: 'min,max')",
)
def cli(
    sources,
    cogeo_profile,
    creation_options,
    options,
    prefix,
    topic,
    resolution,
    layers,
):
    """Create pdal-watchbot."""
    def _create_message(source):
        message = {
            "src_path": source,
            "dst_prefix": prefix,
            "resolution": resolution,
            "output": layers,
            "profile_name": cogeo_profile,
            "profile_options": creation_options,
            "options": options,
        }
        return message

    messages = [_create_message(source) for source in sources]
    parts = _chunks(messages, 50)
    _send_message = partial(sns_worker, topic=topic)
    with futures.ThreadPoolExecutor(max_workers=50) as executor:
        executor.map(_send_message, parts)


if __name__ == "__main__":
    cli()
