# pdal-watchbot

![](https://user-images.githubusercontent.com/10407788/68695040-4e707b00-0548-11ea-89a6-d81a97c4b62c.jpg)


A PDAL fork of https://github.com/developmentseed/cogeo-watchbot-light to convert `.Laz` file to COG at scale.

# What is this

This repo host the code for a serverless architecture enabling creation of Cloud Optimized GeoTIFF at scale.

## Architecture

![](https://user-images.githubusercontent.com/10407788/66224855-f3c04580-e6a4-11e9-8903-8319c9a89875.png)


# Deploy

### Requirements
- serverless
- docker
- aws account


1. Install and configure serverless
```bash
# Install and Configure serverless (https://serverless.com/framework/docs/providers/aws/guide/credentials/)
$ npm install serverless -g 
```

2. (Temporary) Clone PDAL/lambda

```bash
# In pointcloud-to-cog/ directory
git clone https://github.com/PDAL/lambda
cd lambda && git checkout 6eddf86
```

2. Create Lambda package

```bash
# In pointcloud-to-cog/ directory
$ make build
```

3. Deploy the Serverless stack

```bash
$ sls deploy --stage production --bucket my-bucket --region us-east-1

# Get Stack info
$ sls info --bucket my-bucket --verbose
```



# How To

### Example (Montreal Open Data)

1. Get a list of files you want to convert
```$
$ wget http://donnees.ville.montreal.qc.ca/dataset/9ae61fa2-c852-464b-af7f-82b169b970d7/resource/ec35760c-5cbe-44a0-8ad1-30c037174b0a/download/indexlidar2015.csv

# Fix list
$ cat indexlidar2015.csv | grep "http://depot.ville.montreal.qc.ca" | cut -d',' -f3 > list_files.txt
```

2. Use scripts/create_job.py

```
$ pip install rio-cogeo rio-tiler

$ python scripts/create_jobs.py --help 
Usage: create_jobs.py [OPTIONS] [SOURCES]

  Create pdal-watchbot.

Options:
  -p, --cog-profile [jpeg|webp|zstd|lzw|deflate|packbits|lzma|lerc|lerc_deflate|lerc_zstd|raw]
                                  CloudOptimized GeoTIFF profile (default: deflate).
  --co, --profile NAME=VALUE      Driver specific creation options.See the
                                  documentation for the selected GTiff driver for more information.
  --options, --op NAME=VALUE      rio_cogeo.cogeo.cog_translate input options.
  --prefix TEXT                   AWS S3 Key prefix.
  --topic TEXT                    SNS Topic  [required]
  --resolution FLOAT              Length of raster cell edges in X/Y units. (default: 0.25)
  --layers TEXT                   A comma separated list of statistics for
                                  which to produce raster layers. (default: 'min,max')
  --help                          Show this message and exit.
```

```bash

$ cd scripts/
$ cat ../list_files.txt | python -m create_jobs - \
   -p webp \
   --co blockxsize=256 \
   --co blockysize=256 \
   --op overview_level=6 \
   --op dtype=float32 \
   --op web_optimized=True \
   --prefix my-prefix \
   --topic arn:aws:sns:us-east-1:{AWS_ACCOUNT_ID}:pdal-watchbot-production-WatchbotTopic
```

Note: Output files will be saved in the `bucket` defined in the stack. By default (in the CLI) the prefix will be set to `cogs`.

3. Create mosaic (optional)

```
# Install cogeo-mosaic

$ pip install cython==0.28 # (ref: https://github.com/tilery/python-vtzero/issues/13)
$ pip install git+http://github.com/developmentseed/cogeo-mosaic

# Create mosaic

$ aws s3 ls my-bucket/my-prefix/ | awk '{print "s3://my-bucket/my-prefix/"$NF}'  | cogeo-mosaic create - | gzip > mtl.json.gz
```
