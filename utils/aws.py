# aws.py - Misc AWS utility functions

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

import config

version = '0.1'

def s3connect():
    '''Create/open a bucket and return the key'''
    import boto
    import boto.s3.key

    s3 = boto.connect_s3(config.aws_access_key_id,
            config.aws_secret_access_key)
    bucket = s3.create_bucket(config.bucket)
    key = boto.s3.key.Key(bucket)
    
    return key


def create_file_key(filename):
    '''Creates the key to use for S3. Key will be
    [machine_name]/YYYYMMDD/filename'''
    from time import strftime
    return ('%s/%s/%s' % (config.machine_name, strftime('%Y%m%d'), 
        filename))


def create_archive_key(file_extension, backup_type):
    '''Creates and returns the key for S3. Key format is
    machine_name/backup_type/YYYYMMDD.file_extension'''
    from time import strftime
    keyname = ('%s/%s/%s%s' % (config.machine_name, backup_type,
        strftime('%Y%m%d'), file_extension))
    return keyname
