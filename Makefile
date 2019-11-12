
SHELL = /bin/bash

build:
	# This should be removed once https://github.com/PDAL/lambda/issues/6 get solved
	cd lambda; docker build --tag lambda:pdal .; cd ..
	docker build --tag lambda:latest .
	docker run --name lambda -itd lambda:latest /bin/bash
	docker cp lambda:/tmp/package.zip package.zip
	docker stop lambda
	docker rm lambda
