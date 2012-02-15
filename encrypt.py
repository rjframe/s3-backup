# encrypt.py - Encryption/decryption and hash functions

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


import struct

from Crypto.Cipher import AES

import log

log = log.get_logger('encrypt')


def encrypt_file(key, filename, piece_size):
    import os

    encryptor = AES.new(key, AES.MODE_CBC)
    # Store the file size for when we decrypt
    fsize = os.path.getsize(filename)
    enc_file = filename + '.enc'
    
    with open(filename, 'rb') as inf:
        with open(enc_file, 'wb') as outf:
            outf.write(struct.pack('<Q', fsize))
            while True:
                piece = inf.read(piece_size)
                if not piece:
                    break
                # The file size must be a multiple of 16 bytes
                elif len(piece) % 16 != 0:
                    piece += ' ' * (16 - len(piece) % 16)
                outf.write(encryptor.encrypt(piece))
    return enc_file


def decrypt_file(key, encrypted_file, piece_size):
    '''Decrypts and writes a file. Saves the new file with the same name
    minus the last file extension. Basically assumes the file as an '.enc'
    or similar extension. Returns the filename of the decrypted file.'''

    decrypted_file = encrypted_file.rsplit('.', 1)[0]
    
    with open(encrypted_file, 'rb') as inf:
        size = struct.unpack('<Q', inf.read(struct.calcsize('Q')))[0]
        decryptor = AES.new(key, AES.MODE_CBC)

        with open(decrypted_file, 'wb') as outf:
            while True:
                piece = inf.read(piece_size)
                if not piece:
                    break
                outf.write(decryptor.decrypt(piece))
            outf.truncate(size)
    return decrypted_file


# TODO: Place default block sizes here for each hash algorithm
# TODO: Use these in the code
def getFileHash(file, algorithm='SHA512'):
    '''Returns a hexadecimal hash of the given file. Currently supported
    algorithms are "SHA512" and "MD5"'''

    def getSHA512(file):
        '''Returns a hexadecimal-format SHA512 hash.'''
        from Crypto.Hash import SHA512

        hash  = SHA512.new()
        block_size = hash.block_size

        with open(file, 'rb') as f:
            for piece in iter(lambda: f.read(128 * block_size), ''):
                hash.update(piece)
        
        return hash.hexdigest()

    def getMD5(file):
        '''Returns a hexadecimal-format MD5 hash.'''
        from Crypto.Hash import MD5

        hash  = MD5.new()
        block_size = hash.block_size

        with open(file, 'rb') as f:
            for piece in iter(lambda: f.read(128 * block_size), ''):
                hash.update(piece)
        
        return hash.hexdigest()
    
    if algorithm == 'MD5':
        return getMD5(file)
    elif algorithm == 'SHA512':
        return getSHA512(file)
    else:
        log.error('Unsupported hash algorithm given.')
        raise # TODO: Create error class
