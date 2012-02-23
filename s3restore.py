#!/usr/bin/env python
# restore.py - Handles restoration of files backed up by s3backup.py

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

from sys import exit

import config
import log

version = 0.1

log = log.get_logger('s3restore')

# TODO: Accept root from the cmd - default '/' for Un*x and 'C:\' for 
# Windows

def main():
    parser = get_args()
    args = parser.parse_args()
    args.func(args) # Calls the appropriate function


# BEGIN command functions

def run_full_restore(args):
    '''Executes the subcommand "full-restore".'''

    def handle_download(bucket, schedule, date, dest):
        ''' Handles the downloading and decrypting of the archive.'''
        # TODO: Refactor - too much repetition in if/else
        if dest != None:
            # If a destination is given, the --download-only option was
            # passed. We download, decrypt if necessary, then exit
            try:
                archive, is_enc = get_restore_archive(bucket, schedule,
                    date, dest)
                if is_enc:
                    archive = decrypt(archive)
                    log.debug('Archive is valid tar file: {}'.format(
                            tarfile.is_tarfile(archive)))
                    log.info('Saved file to %s.' % archive)
                    exit(0)
            except:
                raise
        else:
            dest = config.dest_location
            archive, is_enc = get_restore_archive(bucket, schedule,
                    date, dest)
            if is_enc:
                archive = decrypt(archive)
            log.debug('Archive is valid tar file: {}'.format(
                    tarfile.is_tarfile(archive)))
            return archive


    import tarfile
    from os.path import exists, join
    from sys import platform

    bucket = s3connect()
    # 'args.download_only' contains either the download path or None
    log.debug('Calling handle_download. args.date = %s' % args.date)
    archive = handle_download(bucket, args.schedule, args.date,
            args.download_only)
    log.debug('Archive: %s' % archive)
    tar = tarfile.open(archive, 'r')
  
    # TODO: How does the Mac do filesystems?
    if platform.startswith('win'):
        if len(args.filesystem) == 1:
            if args.filesystem.isalpha():
                root = args.filesystem.upper()
        else:
            log.error('Invalid filesystem root supplied.')
            exit(1)
    else:
        root = '/'

    if args.force_no_overwrite: # Write all non-existent files
        files = tar.getnames()
        for f in files:
            filepath = join(root, f)

            if not exists(filepath):
                log.info('Extracting %s' % f)
                tar.extract(f, root)
            else:
                log.info('%s exists. Not restoring.' % f)

    elif args.force == True:    # Write/overwrite everything
        tar.extractall(root)
    else:   # Ask on each file
        files = tar.getnames()
        for f in files:
            do_it = raw_input('Restore %s? [y|n] ' % f)
            if do_it.lower() == 'y':
                tar.extract(f, root)


def run_choose_files(args):
    '''Executes the subcommand "choose-files".'''
    pass


def run_browse_files(args):
    '''Execute the subcommand "browse-files".'''
    pass

# END command functions


def s3connect():
    '''Connects to S3 and returns the bucket.'''
    from boto import connect_s3
    #import boto.s3
    
    s3 = connect_s3(config.aws_access_key_id,
            config.aws_secret_access_key)
    return  s3.get_bucket(config.bucket)



def decrypt(archive):
    '''Decrypts the given file. It deletes the encrypted version and
    returns the path to the decrypted file, which is the encrypted filename
    with a '.d' extension appended.'''
    from encrypt import decrypt_file
    from os import remove

    decrypted = archive + '.d'
    if decrypt_file(config.enc_key, archive, decrypted,
            config.enc_piece_size):
        log.debug('Encrypted file: %s' % decrypted)
        remove(archive)
        return decrypted 
    else:
        raise IOError # Failed - TODO: Handle


def get_restore_archive(bucket, schedule, date, path):
    '''Retrieves the archive from S3, saves it in config.dest_location, and
    returns the filename.'''
    import os.path
    import boto.exception

    key, name = build_key(bucket, schedule, date)
    is_encrypted = key.get_metadata('enc')
    
    if os.path.isdir(path):
        archive_path = os.path.join(path, name)
    else:
        log.warn('Invalid path "%s" given. Using default directory %s' %
                (path, config.dest_location))
        archive_path = os.path.join(config.dest_location, name)
    
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except OSError:
        log.error('Cannot create directory %s.' % config.dest_location)
        exit(1)

    try:
        key.get_contents_to_filename(archive_path)
    except boto.exception.S3ResponseError:
        log.error('The archive %s does not exist.' % key.key)
        exit(1)
    return archive_path, is_encrypted


def build_key(bucket, backup_type, backup_date): 
    '''Builds the base S3 directory structure. Returns the key  and
    the name of the file.'''
    # All uploads begin 'machine/backup-type/date.extension' for
    # archive backups.
    # TODO: Determine extension
    from time import strftime, strptime

    if backup_date != 'last':
        try:
            date = strftime('%Y%m%d', strptime(backup_date, '%m %d %Y'))
        except ValueError:
            log.error('Improper date format given.')
            raise # TODO: Implement
    else:

        prefix = ('%s/%s/' % (config.machine_name, backup_type))
        thekey = max(bucket.list(prefix, '/'))
        try:
            date = thekey.key.split('/')[2].split('.')[0]
        except:
            log.error('Invalid archive filename; last backup not known.')
            exit(1)

    extension = 'tar.bz2' 
    backup_name = ('%s.%s' % (date, extension))
    keyname = '%s/%s/%s' % (config.machine_name, backup_type,
            backup_name)
    key = bucket.get_key(keyname)

    return key, backup_name


def get_args():
    import argparse
    from sys import platform

    # Parent parser
    mainparser = argparse.ArgumentParser(description='''Restores backups
            created by s3backup.py''')
    mainparser.add_argument('--version', action='version',
            version='s3restore %s; Suite version %s' %
            (version, config.version))
    subparsers = mainparser.add_subparsers(title='Commands',
            description='Type "command -h" for more info.')

    # Parser for the full-restore command
    fullparser = subparsers.add_parser('full-restore', help='''Restores all
            files from the backup.''')
    fullparser.add_argument('schedule', choices=['daily', 'weekly',
            'monthly'], help='Specifies the backup type to restore.')
    fullparser.add_argument('date', help='''The date the backup was made. A
            quoted string of the format "MM DD YYYY". A value of "last"
            restores the most recent backup.''')
    fullparser.add_argument('--force', action='store_true',
            help='''Restores all files, overwriting any with duplicate
            filenames.''')
    fullparser.add_argument('--force-no-overwrite', action='store_true',
            help='''Restores all file that no longer exist on the
            filesystem.''')
    fullparser.add_argument('-d', '--download-only', metavar='DIR',
            help='''Download and decrypt (if necessary) the archive to the
            given directory, but do not extract.''')
    if platform.startswith('win'):
        fullparser.add_argument('-f', '--filesystem', default='C',
                help='''The filesystem to use. Defaults to "C"''')
    fullparser.set_defaults(func=run_full_restore)

    # Parser for the choose-files command
    chooseparser = subparsers.add_parser('choose-files', help='''Select
    what files to restore.''')
    chooseparser.add_argument('schedule', choices=['daily', 'weekly',
            'monthly'], help='Specifies the backup type to restore.')
    chooseparser.add_argument('date', help='''The date the backup was made.
            A string of the format "MM DD YYYY". A value of "last" restores
            the most recent backup.''')
    chooseparser.add_argument('--force', action='store_true',
            help='''Restores the files without confirming any overwrites.
            ''')
    chooseparser.add_argument('--force-no-overwrite', action='store_true',
            help='''Restores the files, asking to verify overwriting
            files.''')
    chooseparser.add_argument('-f', nargs='*', metavar='FILE',
            help='''Specify one or more files to restore. Only the
            specified files are restored.''')
    chooseparser.set_defaults(func=run_choose_files)

    # Parser for the browse-files command
    browseparser = subparsers.add_parser('browse-files', help='''Browse the
            archives and the archive's files and choose which to restore.
            ''')
    browseparser.add_argument('-t', '--type', choices=['daily', 'weekly',
            'monthly'], help='The type of backup to restore.')
    browseparser.add_argument('-d', '--date', help='''The date the backup
            was made. A string of the format "MM DD YYYY". A value of
            "last" browses the most recent backup.''')
    browseparser.set_defaults(func=run_browse_files)

    return mainparser


if __name__ == '__main__':
     main()
