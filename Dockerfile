FROM lambda:pdal
# image reference should be changed once https://github.com/PDAL/lambda/issues/6 get resolved.

ENV \
  LANG=en_US.UTF-8 \
  LC_ALL=en_US.UTF-8 \
  CFLAGS="--std=c99"

RUN \
    pip3.7 install pip -U \
    && pip3.7 install cython numpy --no-binary numpy

ENV PACKAGE_PREFIX=/tmp/package

################################################################################
#                            CREATE PACKAGE                                    #
################################################################################
COPY app app
COPY setup.py setup.py

RUN pip3.7 install . --no-binary rasterio,numpy -t $PACKAGE_PREFIX

# # Leave module precompiles for faster Lambda startup
RUN find ${PACKAGE_PREFIX}/ -type f -name '*.pyc' | while read f; do n=$(echo $f | sed 's/__pycache__\///' | sed 's/.cpython-[2-3][0-9]//'); cp $f $n; done;
RUN find ${PACKAGE_PREFIX}/ -type d -a -name '__pycache__' -print0 | xargs -0 rm -rf
RUN find ${PACKAGE_PREFIX}/ -type f -a -name '*.py' -print0 | xargs -0 rm -f

RUN cd $PACKAGE_PREFIX && zip -r9q /tmp/package.zip *
