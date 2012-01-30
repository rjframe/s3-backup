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


import argparse
import time
import os.path

import boto
import boto.s3.key

import config


parser = argparse.ArgumentParser(description='''Transfers the given file to
        Amazon S3.''')
parser.add_argument('--list', action='store_false', help='''If the given
        file is a list of files, send each item in the list.''')
parser.add_argument('file_path')


def main():
    args = parser.parse_args()
    
    key = s3connect()
    if args.list:
        pass # TODO: Implmement file list uploads
        print('s3put: Uploading a list of files is not yet supported.')
    else:
        key.key = create_key(os.path.basename(args.file_path))
        key.set_contents_from_filename(file_path)


def create_key(filename):
    '''Key will be [machine_name]/YYYYMMDD/filename'''
    return ('%s/%s/%s' % (config.machine_name, strftime('%Y%m%d'), 
        filename))


def s3connect():
    s3 = boto.connect_s3(config.aws_access_key_id,
            config.aws_secret_access_key)
    bucket = s3.create_bucket(config.bucket)
    key = boto.s3.key.Key(bucket)
    
    return key


if __name__ == '__main__':
    main()
