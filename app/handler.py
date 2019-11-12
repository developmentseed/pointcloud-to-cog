"""Watchbot-light Worker."""

import os
import json

from . import translator


def process(message):
    """Map Step: Create COGs."""
    if isinstance(message, str):
        message = json.loads(message)

    src_path = message["src_path"]
    dst_prefix = message["dst_prefix"]

    bname = os.path.splitext(os.path.basename(src_path))[0]
    out_key = os.path.join(dst_prefix, f"{bname}.tif")
    translator.process(
        src_path,
        os.environ["COG_BUCKET"],
        out_key,
        resolution=message.get("resolution", 0.25),
        output=message.get("output", "min,max"),
        profile=message["profile_name"],
        profile_options=message["profile_options"],
        **message["options"]
    )

    return True


def _parse_message(message):
    if not message.get("Records"):
        return message
    record = message["Records"][0]
    body = json.loads(record["body"])
    return body["Message"]


def main(event, context):
    """
    Handle events.

    Events:
        - SQS queue (MAP)

    """
    message = _parse_message(event)
    return process(message)
