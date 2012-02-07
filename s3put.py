# s3put.py - Transfers files to Amazon S3

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


import os.path

from Crypto.Cipher import AES

import log
import config


log = log.get_logger('s3put')

def main():
    import argparse

    parser = argparse.ArgumentParser(description='''Transfers the given
            file to Amazon S3.''')
    parser.add_argument('--list', action='store_true', help='''If the given
            file is a list of files, send each item in the list. The
            directory tree is preserved so that the files can be restored
            to their original locations.''')
    parser.add_argument('file_path')
    args = parser.parse_args()
    
    key = s3connect()
    key.key = create_key(os.path.basename(args.file_path))
    if args.list:
        # key.key is now a folder. We'll modify the key with each upload to
        # place the files within it
        base = os.path.dirname(key.key)
        
        with open(args.file_path, 'r') as flist:
            files = flist.readlines()
        for f in files:
            f = f.strip()
            key.key = '/' + base + f

            if os.path.isdir(f):
                upload_dir_tree(f, key)
            else:
                key.set_metadata('sha512', getSHA512(f))
                key.set_contents_from_filename(f)


def getSHA512(file):
    '''Returns a hexadecimal-format SHA512 hash of the specified file.'''
    from Crypto.Hash import SHA512

    hash  = SHA512.new()
    block_size = hash.block_size

    with open(file, 'rb') as f:
        for piece in iter(lambda: f.read(128 * block_size), ''):
            hash.update(piece)
    
    return hash.hexdigest()


def upload_dir_tree(dir_tree, key):
    '''Uploads a directory tree rather than a single file.'''
    def visit(_, dir_tree, files):
        log.debug('dirtree\t%s' % dir_tree)
        k = thekey      # Reset key each entry
        for f in files:
            log.debug('f: %s' % f)
            fp = os.path.join(dir_tree, f)
            if os.path.isfile(fp):
                log.debug('reg f:  %s' % fp)
                # For each file, update the key with the path
                key.key = k + os.path.basename(fp)
                key.set_metadata('sha512', getSHA512(fp))
                key.set_contents_from_filename(fp)

    # Execute visit in each directory
    thekey = key.key
    log.debug('uploading tree %s', dir_tree)
    os.path.walk(dir_tree, visit, None)


def create_key(filename):
    '''Key will be [machine_name]/YYYYMMDD/filename'''
    import time

    return ('%s/%s/%s' % (config.machine_name, time.strftime('%Y%m%d'), 
        filename))


def s3connect():
    '''Create/open a bucket and return the key'''
    import boto
    import boto.s3.key

    s3 = boto.connect_s3(config.aws_access_key_id,
            config.aws_secret_access_key)
    bucket = s3.create_bucket(config.bucket)
    key = boto.s3.key.Key(bucket)
    
    return key


if __name__ == '__main__':
    main()
