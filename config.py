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


# Schedule via cron (win: Task Manager) (see README)
# TODO: Write cron example in Readme

# TODO: Place these in /etc/s3backup.cfg or ~/.s3backup.cfg
# TODO: Test with symbolic links (probably have a couple of issues)
# TODO: Test on Windows
# TODO: Find a good os.nice value so we don't slow things down on a busy
# system

import os

from Crypto.Hash import SHA512

# Suite version
version = '0.5.1'

# Company / software name. Used as prefix for logging, eg:
# name.s3Backup ....
company = "sample"

# === AWS Settings === #

aws_access_key_id = ''
aws_secret_access_key = ''
bucket = 'mybucket'

machine_name = 'test1'


# === Directory / Filesystem settings === #

# If base_dir is specified, the others are relative to it; if it is None,
# the others need to be absolute paths
base_dir = '/some/dir'
daily_backup_list = os.path.join(base_dir, 'daily.s3')
weekly_backup_list = os.path.join(base_dir, 'weekly.s3')
monthly_backup_list = os.path.join(base_dir, 'monthly.s3')

dest_location = '/tmp/backup' # os.path.join(base_dir, 'backup') 
log_file = os.path.join(base_dir, 's3backup.log')

# === Backup settings === #

# Note: this deletes the entire dest_location folder
delete_archive_when_finished = True

# TODO: Allow supplying the password on the command-line when restoring

# We hash a memorable password for the encryption key
enc_backup = True
enc_password = 'Some text to be hashed'
enc_hash = SHA512.new()
enc_hash.update(enc_password)

enc_key = enc_hash.digest()[0:32] # Use the first 32 bits
enc_piece_size = 1024*64

# Supported compression methods are none, gz, and bz2
# TODO: Implement zip compression
compression_method = 'bz2'
