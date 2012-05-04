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

version = '0.2'

log = log.get_logger('s3restore')

# TODO: Accept root from the cmd - default '/' for Un*x and 'C:\' for 
# Windows
# TODO: Allow restore from local archive

def main():
    parser = get_args()
    args = parser.parse_args()
    args.func(args) # Calls the appropriate function


# BEGIN command functions

def run_full_restore(args):
    '''Executes the subcommand "full-restore".'''

    def handle_download(bucket, schedule, date, dest):
        ''' Handles the downloading and decrypting of the archive.'''
        
        try:
            if dest != None:
                archive, is_enc = get_restore_archive(bucket, schedule,
                        date, dest)
            else:
                archive, is_enc = get_restore_archive(bucket, schedule,
                        date, config.dest_location)
            
            if is_enc:
                archive = decrypt(archive)
                log.debug('Archive is valid tar file: {}'.format(
                    tarfile.is_tarfile(archive)))
        except:
            raise

        # If a destination is given, the --download-only option was passed.
        # We download, decrypt if necessary, then exit without extracting.
        # Otherwise, return the archive and continue with the restore.
        if dest == None:
            return archive
        else:
            log.info('Saved file to %s.' % archive)
            exit(0)

    import tarfile
    from os.path import exists, join
    from sys import platform

    bucket = s3connect()
    # 'args.download_only' contains either the download path or None
    log.debug('Calling handle_download. args.date = %s' % args.date)
    archive = handle_download(bucket, args.schedule, args.date,
            args.download_only)
    log.debug('Archive: %s' % archive)
  
    if platform.startswith('win'):
        if len(args.filesystem) == 1:
            if args.filesystem.isalpha():
                root = args.filesystem.upper()
        else:
            log.error('Invalid filesystem root supplied.')
            exit(1)
    else:
        root = '/'

    tar = tarfile.open(archive, 'r')

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
    '''Execute the subcommand "browse-files". Raises any errors.'''
   
    def handle_download(bucket, schedule, date):
        '''Handles the downloading and decrypting of the archive.
        Raises any errors.'''

# TODO: Instead of printing filenames, I want to get the date and list the
# dates backups were made. Probably allow selecting one here and browsing it
        if args.archives:
            print('Implement browse archives')
            exit(0)

        try:
            archive, is_enc = get_restore_archive(bucket, schedule, date,
                    config.dest_location)

            if is_enc:
                archive = decrypt(archive)
                log.debug('Archive is valid tar file: {}'.format(
                        tarfile.is_tarfile(archive)))
        except:
            raise

        return archive


    def run_browse_shell(tarinfo_list):
        '''Allows the user to browse the archive and select the files
        to restore.'''

        help_text = \
'''\n"restore [number]" marks an object for restoration.
"cancel [number]" cancels a marked restoration.
Previous commands: where "number" is the number printed on the listing.

"show" prints all files in the archive.
"show restore" shows all files currently marked for restoration.
"page" prints the archive's files thirty at a time.
"page restore" prints the files marked for restoration, thirty at a time.
"q" quits without restoring.
"finish" quits and restores the files.
"h" shows this message. All commands are case-sensitive.\n\n'''

        from datetime import datetime

        output_format = '{0:<3}{1}{2:50}{3:<6}{4:%Y-%m-%d %H:%M:%S}'

        print(help_text)
        
        go = True
        restore_list = []
        while go:


            # TODO: Refactor the show and page commands
            try:
                inp = raw_input('\n-> ').lower()
                if inp == 'h':
                    print(help_text)

                # Quit, no restore
                elif inp == 'q':
                    go = False
                    restore_list = None
                
                # Quit and restore
                elif inp == 'finish':
                    go = False
                
                # Mark a file for restoration
                elif inp.startswith('restore'):
                    num = inp.split(' ', 1)[1]
                    if num.isdigit():
                        if tarinfo_list[int(num) -1] not in restore_list:
                            restore_list.append(tarinfo_list[int(num) - 1])
                        else:
                            print('That file is already marked.')
                    else:
                        print('I do not know what file you are \
                                referring to.\n')
               
                # Cancel a marked file
                elif inp.startswith('cancel'):
                    num = inp.split(' ', 1)[1]
                    if num.isdigit():
                        if tarinfo_list[int(num) - 1] in restore_list:
                            restore_list.remove(tarinfo_list[int(num) - 1])
                    else:
                        print('I do not know what file you are \
                                referring to.\n')
                
                # Prints the list of objects in the archive or restore list
                elif inp.startswith('show'):
                    try:
                        show_restore = inp.split(' ', 1)[1] == 'restore'
                    except IndexError:
                        show_restore = False
                    
                    if show_restore:
                        # Printing the files in the restore list
                        cnt = 0
                        marked = '' # This lets me use the same format
                        for ti in restore_list:
                            cnt += 1
                            print(output_format.format(
                                    cnt, marked, ti.name, ti.size,
                                    datetime.fromtimestamp(ti.mtime)))
                    else:
                        # We're printing the files in the archive
                        cnt = 0
                        for ti in tarinfo_list:
                            cnt += 1

                            if ti in restore_list:
                                marked = '*'
                            else:
                                marked = ' '
                            print(output_format.format(
                                    cnt, marked, ti.name, ti.size,
                                    datetime.fromtimestamp(ti.mtime)))

                # Page the file list. 30 lines per page.
                elif inp.startswith('page'):
                    try:
                         page_restore = inp.split(' ')[1] == 'restore'
                    except IndexError:
                        page_restore = False

                    if page_restore:
                        # We page the files marked for restoration
                        print('Implement page restore')
                    else:
                        # Paging the archive contents
                        go = True
                        last = 0
                        while go:
                            for i in range(30): 
                                try:
                                    ti = tarinfo_list[last]
                                except IndexError:
                                    go = False
                                    break
                                
                                if ti in restore_list:
                                    marked = '*'
                                else:
                                    marked = ' '
                                print(output_format.format(last + 1,
                                        marked, ti.name, ti.size,
                                        datetime.fromtimestamp(ti.mtime)))
                                   
                                last += 1
                            inp2 = raw_input(
                                        '\nq to quit, Enter to continue: ')
                            if inp2 == 'q':
                                go = False

                else:
                    print('I do not understand that command.\n\n')
            except IndexError:
                print('There is no file with that index.\n')
            except:
                raise

        return restore_list


    import tarfile
    from os.path import exists, join
    from sys import platform

    bucket = s3connect()
    archive = handle_download(bucket, args.schedule, args.date)
    log.debug('Archive: %s' % archive)

    tar = tarfile.open(archive)
    lst = tar.getmembers()

    # Allow the user to browse the archive and select files to extract
    lst_to_extract = run_browse_shell(lst)
    
    #Testing
    print(lst_to_extract)



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
        log.critical('Failed to decrypt the archive %s.' % archive)
        exit(1)


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
            exit(1)
    else:
        # Grab the most recent backup
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
    browseparser.add_argument('-s', '--schedule', choices=['daily',
            'weekly', 'monthly'], help='The type of backup to restore.')
    browseparser.add_argument('-d', '--date', help='''The date the backup
            was made. A string of the format "MM DD YYYY". A value of
            "last" browses the most recent backup.''')
    browseparser.add_argument('--archives', action='store_true',
            help='''Prints the list of archives. If given, all other
            arguments are ignored.''')
    browseparser.set_defaults(func=run_browse_files)

    return mainparser


if __name__ == '__main__':
    main()
