# config.py - Configuration info for s3backup et al

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


# Schedule via cron (win: Task Manager) (see README) TODO: Instructions in
                                                            # Readme

# TODO: Place these in /etc/s3backup.cfg or ~/.s3backup.cfg
# TODO: Logging
# TODO: Test with symbolic links (probably have a couple of issues)
# TODO: Test on Windows


import os


aws_access_key_id = ''
aws_secret_access_key = ''


# Enter client's info here
bucket = 'mybucket'
machine_name = 'test1'

# Note: boto uses TSL by default; we're not going to allow turning it off
# use_tls = True

# If base_dir is specified, the others are relative to it; if it is None,
# the others need to be absolute paths
base_dir = '/home/user'
daily_backup_list = os.path.join(base_dir, 'daily.s3')
weekly_backup_list = os.path.join(base_dir, 'weekly.s3')
monthly_backup_list = os.path.join(base_dir, 'monthly.s3')

# Destination of the created archive
dest_location = '/tmp/backup' # os.path.join(base_dir, 'backup') 

# Log file location
log_file = os.path.join(base_dir, 's3backup.log')

# Compression options
# Note: use_archive = True to tar the files then compress; False for
# for no compression
# Supported compression methods are none, gz, and bz2
# TODO: Implement zip compression

# Note: invalid compression methods should raise tarfile.CompressionError;
# in practice it just hasn't written the file.
use_archive = True # TODO: 'False' not yet implemented
compression_method = 'bz2'
delete_archive_when_finished = True

# END s3backup.py -specific configuration
