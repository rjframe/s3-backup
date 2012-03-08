# s3usercfg.py - Manage user AWS permissions

# Copyright 2012 Ryan Frame

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# TODO: Once the config file is set up, offer to save the keys
# TODO: Set the bucket name to the username?

# TODO:
    # COMPLETE - Create user
    # COMPLETE - Create access keys
        # Save access keys
    # Set permissions
    # Test permissions

import boto.iam.connection
import log

version = '0.1'

log = log.get_logger('s3usercfg')

def main():
    args = get_args()

    # For the moment/testing: REMOVE
    from config_personal import aws_access_key_id, aws_secret_access_key
    args.access = aws_access_key_id
    args.secret = aws_secret_access_key
    # End REMOVE   

    if not args.access: args.access = raw_input('Admin Access key: ')
    if not args.secret: args.secret = raw_input('Admin Secret key: ')

    try:
        conn = boto.iam.connection.IAMConnection(args.access, args.secret)
        acc, sec = create_user(conn, args.user, args.group)
        set_permissions(conn, acc, sec)
    except:
        raise # TODO

    success = test_permissions(conn, acc, sec)
    if success:
        # Will need args.user, acc, sec
        save_config()


def create_user(conn, username, group):
    '''Creates a user with the specified name and returns the new access
    and secret keys.'''
    from boto.connection import BotoServerError
    from sys import exit

    # Returns the response, which seems to include an access key, but not
    # the one we'll have after create_access_key() - probably won't need tmp
    try:
        tmp = conn.create_user(username)
    except BotoServerError:
        log.error('The user %s already exists. Exiting.' % username)
        exit(1) # TODO: Prompt to continue then modify the current user?

    access_info = conn.create_access_key(username)
    access = access_info.access_key_id
    secret = access_info.secret_access_key
    log.debug('Keys: %s, %s' % (access, secret))
    
    return access, secret


def set_permissions(conn, access, secret):
    '''Sets the permissions of the user to only allow read/write access to
    the bucket in config.bucket'''
    pass


def test_permissions(conn, acc, sec):
    '''Test to ensure that (1) we have full control over out bucket and
    that (2) we have no control over any other bucket. Returns True on
    success, False otherwise.'''
    pass
    return True # For now


# TODO: Once the config file is set up; for now, just print everything to
# stdout
def save_config():
    '''Saves all the configuration settings to the config file.'''
    # Force save:
        # Access & secret keys
    # Allow override (prompt first):
        # bucket name = username
    pass
    

def get_args():
    '''Returns the command-line arguments'''
    import argparse

    parser = argparse.ArgumentParser(description='''Creates and configures
            an AWS user for the s3backup suite.''')
    parser.add_argument('user', help='The name of the user to create.')
    parser.add_argument('-g', '--group', help='''The name of the group to
            place the user into. The group must exist.''')
#   TODO: Allow the keys to be read from a file
#    parser.add_argument('--keys', help='''A file that has the administrator
#            access and secret keys.''')
    parser.add_argument('--access', help='''The AWS administrator access
            key to use to create the user. If not given, you will be
            prompted for the key.''')
    # Not much of a secret on the cmd-line, is it?
    parser.add_argument('--secret', help='''The AWS administrator secret
            key to use to create the user. If not given, you will be
            prompted for the key.''')
    return parser.parse_args()


if __name__ == '__main__':
    main()
