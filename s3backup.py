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

import config
import utils.log
import utils.encrypt

version = '0.9'

log = utils.log.get_logger('s3backup')


def main():
    import argparse

    parser = argparse.ArgumentParser(description='''Creates archives of
            files according to a cron-determined schedule.''')
    parser.add_argument('schedule', choices=['daily', 'weekly', 'monthly'])
    parser.add_argument('--version', action='version', version='s3backup '
            '%s; Suite version %s' % (version, config.version))
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
        archive_path, tar_type = create_archive(files)
        if config.enc_backup:
            # We don't add the enc extension to the key - the metadata
            # will tell us whether the archive is encrypted.
            enc_file = utils.encrypt.encrypt_file(config.enc_key,
                    archive_path, config.enc_piece_size)
            send_file(enc_file, tar_type, schedule)
            # Delete the plaintext local version
            os.remove(archive_path)
        else: # Not encrypting
            send_file(archive_path, tar_type, schedule)

        if config.delete_archive_when_finished:
            rmtree(config.dest_location)
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

    try:
        if not os.path.exists(config.dest_location):
            os.makedirs(config.dest_location)
    except OSError:
        log.critical('Cannot create directory %s' % config.dest_location)
        sys.exit(1)

    if config.compression_method == 'zip':
        archive_type = '.zip'
    else:
        archive_type = '.tar'
        mode = 'w:'
        if config.compression_method != 'none':
            archive_type = archive_type + '.' + config.compression_method
            mode += config.compression_method

    archive_name = ('bak' + time.strftime('%Y%m%d') + archive_type)
    archive_name = os.path.join(config.dest_location, archive_name)
   
    if config.compression_method == 'zip':
        create_zip(archive_name, files)
    else:
        create_tar(archive_name, files, mode)

    return archive_name, archive_type


def create_zip(archive, files):
    '''Creates a zip file containing the files being backed up.'''
    import zipfile

    try:
        with zipfile.ZipFile(archive, 'w') as zipf:
            zipf.comment = 'Created by s3-backup'
            for f in files:
                f = f.strip()
                if os.path.exists(f):
                    zipf.write(f)
                    log.debug('Added %s.' % f)
                else:
                    log.error('%s does not exist.' % f)
    except zipfile.BadZipfile:
        # I assume this only happens on reads?
        log.critical('The zip file is corrupt.')
    except zipfile.LargeZipFile:
        log.critical('The zip file is greater than 2 GB.'
                ' Enable zip64 functionality.')

def create_tar(archive, files, mode):
    '''Creates a tar archive of the files being backed up.'''
    import tarfile

    try:
        with tarfile.open(archive, mode) as tar:
            for f in files:
                f = f.strip()
                if os.path.exists(f):
                    tar.add(f)
                    log.debug('Added %s.' % f)
                else:
                    log.error('%s does not exist.' % f)
    except tarfile.CompressionError:
        log.critical('There was an error compressing the backup archive. '
                'Please try again.')
        sys.exit(1)
    except tarfile.TarError:
        log.critical('There was an error creating the backup archive. '
                'Please try again.')
        sys.exit(1)


def send_file(path, tar_type, backup_schedule):
    """Uses s3put.py to send a file to Amazon S3"""
    # First we have to create a connection to S3
    from s3put import s3connect

    key = s3connect()
    key.key = create_key(tar_type, backup_schedule)
    key.set_metadata('sha512', utils.encrypt.getFileHash(path))
    key.set_metadata('enc', str(config.enc_backup))
    log.debug('key: %s' % key)
    log.debug('meta:enc: %s' % key.get_metadata('enc'))
    key.set_contents_from_filename(path)


def create_key(file_extension, backup_type):
    '''Creates and returns the key for S3. Key format is
    machine_name/backup_type/YYYYMMDD.file_extension'''
    keyname = ('%s/%s/%s%s' % (config.machine_name, backup_type,
        time.strftime('%Y%m%d'), file_extension))
    return keyname


if __name__ == "__main__":
    main()
