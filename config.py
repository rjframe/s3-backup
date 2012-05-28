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

# TODO: Test with symbolic links (probably have a couple of issues)
# TODO: Test on Windows
# TODO: Find a good os.nice value so we don't slow things down on a busy
# system

from ConfigParser import SafeConfigParser
import os

scp = SafeConfigParser()
scp.read('s3backup.conf')

# Suite version
version = '0.8'

# === Company Settings === #

# Company / software name. Used as prefix for logging, eg:
# name.s3Backup ....
company = scp.get('Company', 'company')

# === AWS Settings === #

# Read the keys from a file; The first is the access key, the second is
# the secret key
keypath = scp.get('AWS', 'keypath')
with open(keypath, 'r') as inf:
    aws_access_key_id = inf.readline().strip()
    aws_secret_access_key = inf.readline().strip()

bucket = scp.get('AWS', 'bucket_name')
machine_name = scp.get('AWS', 'machine_name')

# === Directory / Filesystem settings === #

base_dir = scp.get('Directory', 'base_directory')
daily_backup_list = os.path.join(base_dir, scp.get('Directory',
                'daily_list'))
weekly_backup_list = os.path.join(base_dir, scp.get('Directory',
                'weekly_list'))
monthly_backup_list = os.path.join(base_dir, scp.get('Directory',
                'monthly_list')) 

dest_location = scp.get('Directory', 'destination')
log_file = scp.get('Directory', 'log_path')

# === Backup settings === #

log_raise_errs = scp.get('Backup', 'raise_log_errors')

# Note: this deletes the entire dest_location folder
delete_archive_when_finished = scp.get('Backup', 'delete_archive')

pass_hash = scp.get('Backup', 'passwd_hash_type')

# Import the proper module and initialize pass_hash
if pass_hash == 'SHA512':
    from Crypto.Hash import SHA512
    pass_hash = SHA512.new()
elif pass_hash == 'MD5':
    from Crypto.Hash import MD5
    pass_hash = MD5.new()
elif pass_hash == 'SHA256':
    from Crypto.Hash import SHA256
    pass_hash = SHA256.new()
else:
    from Crypto.Hash import SHA
    pass_hash = SHA.new()
    
# We hash a memorable password for the encryption key
enc_backup = scp.get('Backup', 'use_encryption')
enc_password = scp.get('Backup', 'encryption_password')
pass_hash.update(enc_password)

enc_key = pass_hash.digest()[0:32] # Use the first 32 bits
enc_piece_size = 1024*64

# Supported compression methods are none, gz, bz2, and zip
compression_method = scp.get('Backup', 'compression')
