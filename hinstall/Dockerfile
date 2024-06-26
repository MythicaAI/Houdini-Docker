# FIRST STAGE: Download Houdini
FROM python:3.11-slim AS houdini-downloader
WORKDIR /code
COPY . ./hinstall
ARG DL_URL
ENV SIDEFX_DL_URL=$DL_URL
ARG DL_NAME
ENV SIDEFX_DL_NAME=$DL_NAME
ARG DL_HASH
ENV SIDEFX_DL_HASH=$DL_HASH
RUN pip install --upgrade --no-cache-dir -r hinstall/requirements.txt
# Set the PYTHONPATH environment variable to include the hinstall directory
ENV PYTHONPATH=/code
RUN mkdir /houdini
RUN python3 hinstall/houinstall.py

# SECOND STAGE: Install and initialize Houdini
FROM debian:12-slim as houdini-install

# Update and install required packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends iputils-ping netcat-openbsd inetutils-telnet inetutils-ftp procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install -y libglu1 libsm6 bc wget libnss3 libxcomposite1 libxrender1 libxrandr2 libfontconfig1 libxcursor1 libxi6 libxtst6 libxkbcommon0 libxss1 libpci3 libasound2 libgl1 libxdamage1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=houdini-downloader /houdini /houdiniInstaller
# Please update the following EULA_DATE to match the latest updated
# date of EULA in yyyy-mm-dd format. E.g. "2020-05-05"
# For Houdini 18.0 and previous version, EULA_DATE should be left empty
ARG EULA_DATE="2021-10-13"
# Force progress on all optional queries
RUN yes | /houdiniInstaller/build/houdini.install --auto-install --accept-EULA ${EULA_DATE} --make-dir /opt/houdini/build
RUN rm -r /houdiniInstaller

# THIRD STAGE: Copy houdini-install image and un-cache unnecessary installation files
FROM debian:12-slim
COPY --from=houdini-install / /
ENV PATH="${PATH}:/opt/houdini/build/houdini/sbin:/opt/houdini/build/bin"