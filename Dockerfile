###############################################################################
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
###############################################################################

FROM python:3.9.20-slim

LABEL maintainer="tomkralidis@gmail.com"

# copy the app
COPY . /app

# Update and upgrade all packages to their latest versions
RUN apt-get update \
    && apt-get install python3-setuptools python3-pip -y --no-install-recommends \
    && apt-get upgrade python3-setuptools python3-pip -y --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade setuptools to a safe version
RUN pip3 install --upgrade setuptools>=70.0.0
    
# install wis2box_auth
RUN cd /app \
    && pip3 install -r requirements.txt \
    && pip3 install -e .

COPY ./entrypoint.sh /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]
