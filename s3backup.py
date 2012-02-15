# s3backup.py - Creates archives of files according to a cron-determined
# schedule

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


import os
import sys
import time
import struct

import config
import log
import s3put
import encrypt

log = log.get_logger('s3backup')


def main():
    import argparse

    parser = argparse.ArgumentParser(description='''Creates archives of
            files according to a cron-determined schedule.''')
    parser.add_argument('schedule', choices=['daily', 'weekly', 'monthly'])
    args = parser.parse_args()

    do_backup(args.schedule)


def do_backup(schedule):
    '''Handles the backup.'''
    
    from shutil import rmtree

    if schedule == 'daily':
        backup_list = config.daily_backup_list
    elif schedule == 'weekly':
        backup_list = config.weekly_backup_list
    else:
        backup_list = config.monthly_backup_list

    try:
        files = read_file_list(backup_list)
        if config.use_archive:
            archive_path, tar_type = create_archive(files)
            if config.enc_backup:
                enc_file = encrypt.encrypt_file(config.enc_key,
                        archive_path, config.enc_piece_size)
                send_file(enc_file, tar_type, schedule)
                # Delete the plaintext local version
                os.remove(archive_path)
            else: # Not encrypting
                send_file(archive_path, tar_type, schedule)

            if config.delete_archive_when_finished:
                rmtree(config.dest_location)
        else:
            # TODO: Implement individual uploads
            log.error('Not yet implemented: individual file uploads.')
    except IOError:
        log.critical('Cannot open file: %s' % backup_list)
        sys.exit(1) 


def read_file_list(flist):
    """Reads and returns the list of files in the file specified by
    'type'. Raises errors to the calling function."""
    with open(flist, 'r') as f:
        data = f.readlines()
    return data


def create_archive(files):
    """Creates an archive of the given files and stores them in
    the location specified by config.destination. Returns the full path of
    the archive."""
    import tarfile

    try:
        if not os.path.exists(config.dest_location):
            os.makedirs(config.dest_location)
    except OSError:
        # TODO: Fallback to temporary directory?
        log.critical('Cannot create directory %s' % config.dest_location)
        sys.exit(1)
    
    archive_type = '.tar'
    mode = 'w:'
    if config.compression_method != 'none':
        archive_type = archive_type + '.' + config.compression_method
        mode += config.compression_method

    archive_name = ('bak' + time.strftime('%Y%m%d') + archive_type)
    archive_name = os.path.join(config.dest_location, archive_name)
    # TODO: I need to verify the file was written also. In tests
    # CompressionError hasn't been raised - it just doesn't write the file.
    try:
        with tarfile.open(archive_name, mode) as tar:
            for f in files:
                f = f.strip()
                if os.path.exists(f):
                    tar.add(f)
    except tarfile.CompressionError:
        raise # TODO: Handle
    except tarfile.TarError:
        raise # TODO: Handle

    return archive_name, archive_type


def send_file(path, tar_type, backup_schedule):
    """Uses s3put.py to send a file to Amazon S3"""
    # First we have to create a connection to S3
    key = s3put.s3connect()
    key.key = create_key(tar_type, backup_schedule)
    key.set_metadata('sha512', encrypt.getFileHash(path))
    key.set_contents_from_filename(path)


def create_key(file_extension, backup_type):
    '''Creates and returns the key for S3. Key format is
    machine_name/backup_type/YYYYMMDD.file_extension'''
    keyname = ('%s/%s/%s%s' % (config.machine_name, backup_type,
        time.strftime('%Y%m%d'), file_extension))
    return keyname


if __name__ == "__main__":
    main()
