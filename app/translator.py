"""translator."""

import os
import uuid
from urllib.parse import urlparse

import wget

from boto3.session import Session as boto3_session

from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles

REGION_NAME = os.environ.get("AWS_REGION", "us-east-1")


def _s3_download(path, key):
    session = boto3_session(region_name=REGION_NAME)
    s3 = session.client("s3")
    url_info = urlparse(path.strip())
    s3_bucket = url_info.netloc
    s3_key = url_info.path.strip("/")
    s3.download_file(s3_bucket, s3_key, key)
    return True


def _upload(path, bucket, key):
    session = boto3_session(region_name=REGION_NAME)
    s3 = session.client("s3")
    with open(path, "rb") as data:
        s3.upload_fileobj(data, bucket, key)
    return True


def to_tiff(src_path, dst_path, resolution=0.25, output="min,max"):
    """Run PDAL Translate."""
    os.system(
        f"/opt/bin/pdal translate {src_path} {dst_path} --writers.gdal.dimension=Z --writers.gdal.resolution={resolution} --writers.gdal.gdalopts=COMPRESS=DEFLATE --writers.gdal.output_type={output} --nostream"
    )
    return True


def to_cog(src_path, dst_path, profile="deflate", profile_options={}, **options):
    """Convert image to COG."""
    output_profile = cog_profiles.get(profile)
    output_profile.update(dict(BIGTIFF="IF_SAFER"))
    output_profile.update(profile_options)

    config = dict(
        GDAL_NUM_THREADS="ALL_CPUS",
        GDAL_TIFF_INTERNAL_MASK=True,
        GDAL_TIFF_OVR_BLOCKSIZE="128",
    )

    cog_translate(
        src_path,
        dst_path,
        output_profile,
        config=config,
        in_memory=False,
        quiet=True,
        allow_intermediate_compression=True,
        **options,
    )
    return True


def process(
    url,
    out_bucket,
    out_key,
    resolution=0.25,
    output="min,max",
    profile="deflate",
    profile_options={},
    **options
):
    """Download, convert and upload."""
    os.system("rm -rf /tmp/*.tif")

    url_info = urlparse(url.strip())
    if url_info.scheme not in ["http", "https", "s3"]:
        raise Exception(f"Unsuported scheme {url_info.scheme}")

    src_path = "/tmp/" + os.path.basename(url_info.path)
    if url_info.scheme.startswith("http"):
        wget.download(url, src_path)
    elif url_info.scheme == "s3":
        _s3_download(url, src_path)

    uid = str(uuid.uuid4())

    dst_path = f"/tmp/{uid}.tif"
    to_tiff(src_path, dst_path, resolution=resolution, output=output)
    os.remove(src_path)

    cog_path = f"/tmp/{uid}_cog.tif"
    to_cog(
        dst_path,
        cog_path,
        profile=profile,
        profile_options=profile_options,
        **options
    )

    _upload(cog_path, out_bucket, out_key)

    # cleanup
    os.system("rm -rf /tmp/*.tif")

    return True
