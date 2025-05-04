# Thanks to ChatGPT for this code

import hashlib

# Custom base64 encoding table used by md5crypt
ITOA64 = "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

def to64(v, n):
    result = ''
    while n > 0:
        result += ITOA64[v & 0x3f]
        v >>= 6
        n -= 1
    return result

def md5crypt(password, salt, magic="$1$"):
    """
    Encrypts a password using the md5crypt algorithm.
    """
    # Trim salt if longer than 8 characters
    salt = salt[:8]
    
    # Initial hash: password + magic + salt
    m = hashlib.md5()
    m.update(password.encode('utf-8') + magic.encode('utf-8') + salt.encode('utf-8'))

    # Alternate sum: password + salt + password
    alt = hashlib.md5(password.encode('utf-8') + salt.encode('utf-8') + password.encode('utf-8')).digest()

    # Add alternate sum into m
    for i in range(len(password)):
        m.update(alt[i % 16:i % 16 + 1])

    # Obscure step
    i = len(password)
    while i:
        if i & 1:
            m.update(b'\x00')
        else:
            m.update(password.encode('utf-8')[0:1])
        i >>= 1

    final = m.digest()

    # 1000 rounds
    for i in range(1000):
        md = hashlib.md5()
        if i % 2:
            md.update(password.encode('utf-8'))
        else:
            md.update(final)
        if i % 3:
            md.update(salt.encode('utf-8'))
        if i % 7:
            md.update(password.encode('utf-8'))
        if i % 2:
            md.update(final)
        else:
            md.update(password.encode('utf-8'))
        final = md.digest()

    # Rearranged base64 output
    parts = [
        to64((final[0]<<16) | (final[6]<<8) | final[12], 4),
        to64((final[1]<<16) | (final[7]<<8) | final[13], 4),
        to64((final[2]<<16) | (final[8]<<8) | final[14], 4),
        to64((final[3]<<16) | (final[9]<<8) | final[15], 4),
        to64((final[4]<<16) | (final[10]<<8) | final[5], 4),
        to64(final[11], 2)
    ]

    return magic + salt + '$' + ''.join(parts)

