# misc.py - Miscellaneous utility functions without a definite category

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

version = '0.1'

def get_hash_file_path(archive_name):
    '''Returns the full path of the hash file'''
    from os.path import basename, join
    from config import hash_file_path

    hash_file_name = basename(archive_name + '.hash')
    return join(hash_file_path, hash_file_name)


def add_file_hash(archive_name, filename):
    '''Adds the hash of the given file to a hash file in the
    directory specified in the configuration file.'''
    
    def get_hash_line(file, hash):
        from utils.encrypt import get_file_hash
        hash = get_file_hash(file)
        return ('%s\t%s\n' % (file, hash))

    import os.path
    from time import strftime

    hash_file = get_hash_file_path(archive_name)

    if not os.path.exists(hash_file):
        mode = 'w'
    else:
        mode = 'a'

    if os.path.isdir(filename):
        import os
        with open(hash_file, mode) as hf:
            for root, dirs, files in os.walk(hash_file):
                for f in files:
                    hf.write(get_hash_line(os.path.join(root, f), hash))
    else:
        with open(hash_file, mode) as hf:
            hf.write(get_hash_line(filename, hash))
