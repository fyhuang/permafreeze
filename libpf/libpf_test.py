import libpf

uukey, size = libpf.hash_and_size('framing_format.txt')
assert uukey == 'e57d4fdb99841cb565edad94cc89af1c3691fd34e6f7a8223ba321824e9a2a471c2b0caa43a3ede6fa7e49cb43bb023ca8f1c71e0455e8c30dc9c70b214d93c2'
assert size == 4634

test_str = 'Hello, world! This is a test string for libpf and SnappyFd. Test test test test.'

sfd = libpf.SnappyFd('test.sz', libpf.MODE_COMPRESS)
sfd.write(test_str)
sfd.close()
