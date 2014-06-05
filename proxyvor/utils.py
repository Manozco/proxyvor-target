"""
various utils methods
"""
import uuid
import sys
import os
import json
import logging

LOGGER = logging.getLogger()


def validate_uuid4(uuid_string):
    """
    Validate that a UUID string is in
    fact a valid uuid4.
    It is vital that the 'version' kwarg be passed
    to the UUID() call, otherwise any 32-character
    hex string is considered valid.
    """
    try:
        val = uuid.UUID(uuid_string, version=4)
    except ValueError:
        # If it's a value error, then the string
        # is not a valid hex code for a UUID.
        return False
    if '-' in uuid_string:
        uuid_string = uuid_string.replace('-', '')
    return str(val.hex) == uuid_string


def signal_handler(signal, frame):
    # pylint: disable=unused-argument
    """
    basic signal handler
    """
    print 'You pressed Ctrl+C!'
    sys.exit(0)


def save_on_disk(tokens, path):
    """
    save tokens in the directory path
    """
    for token in tokens:
        if tokens[token] != {}:
            json_string = ""
            try:
                json_string = json.dumps({'token': token, 'data': tokens[token]},
                                         sort_keys=True, indent=4, separators=(',', ': '))
            except TypeError:
                LOGGER.warn("Can not dump token as json: {}".format(token))
            filepath = os.path.join(path, token)
            token_file = open(filepath, 'w')
            token_file.write(json_string)
            token_file.close()


def read_tokens_on_start(path):
    """
    read all the files in path and return a map containing the token read
    """
    ret_tokens = {}
    for file_name in os.listdir(path):
        if not validate_uuid4(file_name):
            continue
        filepath = os.path.join(path, file_name)
        token_file = open(filepath, 'r')
        file_content = token_file.read()
        token_file.close()
        if len(file_content) == 0:
            LOGGER.info('file {0} is empty'.format(file_name))
            continue
        json_content = None
        try:
            json_content = json.loads(file_content)
        except ValueError:
            continue
        if (json_content['token'] is None or json_content['token'] != file_name or
            json_content['data'] is None):
            LOGGER.warn('invalid data in: {}'.format(file_name))
            continue
        ret_tokens[json_content['token']] = json_content['data']
    return ret_tokens
