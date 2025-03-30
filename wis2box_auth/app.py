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

from flask import Flask, request
import logging
import os
from typing import Tuple

from wis2box_auth import (
    is_token_authorized,
    is_resource_open,
    create_token,
    delete_token,
    extract_topic
)
from wis2box_auth.log import setup_logger

LOGGER = logging.getLogger(__name__)
app = Flask(__name__)

LOGLEVEL = os.environ.get('WIS2BOX_LOGGING_LOGLEVEL', 'ERROR')
LOGFILE = os.environ.get('WIS2BOX_LOGGING_LOGFILE', 'stdout')
setup_logger(LOGLEVEL, LOGFILE)
app.secret_key = os.urandom(32)


def get_response(code: int, description: str) -> Tuple[dict, int]:
    """
    Generate wis2box-auth response

    :param code: `int` of HTTP response status
    :param description: `str` of response description

    :returns: `Tuple` of wis2box-auth response instance
    """

    return {'code': code, 'description': description}, code


@app.route('/authorize')
def authorize():
    api_key = None
    request_uri = request.headers.get('X-Forwarded-Uri')
    request_ = request.from_values(request_uri)

    metadata_collections = [
        'data/metadata',
        'discovery-metadata',
        'stations'
    ]

    if (request.headers.get('X-Forwarded-Method', 'GET') == 'GET' and
            any([x in request_uri for x in metadata_collections])):
        LOGGER.debug('API metadata request')
        msg = 'Resource is open'
        LOGGER.debug(msg)
        return get_response(200, msg)

    LOGGER.debug('Extracting topic from request URI')
    resource = extract_topic(request_uri)

    LOGGER.debug('Extracting API token')
    auth_header = request.headers.get('Authorization')
    if request_.args.get('token'):
        api_key = request_.args.get('token')
    elif auth_header is not None and 'Bearer' in auth_header:
        api_key = auth_header.split()[-1].strip()

    # check if resource passed exists in auth list
    # if no, it's open, return
    if resource is None or is_resource_open(resource):
        msg = 'Resource is open'
        LOGGER.debug(msg)
        return get_response(200, msg)

    LOGGER.debug(f'Request for restricted resource: {resource}')
    # if yes, check that api key exists
    # if no, return 401
    if api_key is None:
        msg = 'Missing API key'
        LOGGER.debug(msg)
        return get_response(401, msg)

    # check that API key can access the resource
    if is_token_authorized(resource, api_key):
        msg = f'Access granted for {resource}'
        LOGGER.debug(msg)
        return get_response(200, msg)
    else:
        msg = f'Access denied for {resource}'
        LOGGER.debug(msg)
        return get_response(401, msg)


@app.route('/add_token', methods=['POST'])
def add_token():
    """Add access token for a topic"""

    token = request.form.get('token')
    topic = request.form.get('topic')

    if create_token(topic, token):
        msg = f'Access token created for {topic}'
        LOGGER.debug(msg)
        return get_response(200, msg)
    else:
        msg = f'Failed to create access token {topic}'
        LOGGER.debug(msg)
        return get_response(400, msg)


@app.route('/remove_token', methods=['POST'])
def remove_token():
    """Delete one to many tokens for a topic"""

    token = request.form.get('token')
    topic = request.form.get('topic')

    if delete_token(topic, token):
        msg = f'Access token(s) deleted for {topic}'
        LOGGER.error(msg)
        return get_response(200, msg)
    else:
        msg = f'Failed to remove access token(s) for {topic}'
        LOGGER.error(msg)
        return get_response(400, msg)


if __name__ == '__main__':
    app.run()
