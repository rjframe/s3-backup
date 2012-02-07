import struct

from Crypto.Cipher import AES


def decrypt_file(key, encrypted_file, piece_size):
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
