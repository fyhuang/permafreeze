#include <cstdio>

#include <string>
#include <vector>

#define DIV_RNDUP(a, b) (((a) + ((b)-1)) / (b))

const int MODE_COMPRESS = 0;
const int MODE_DECOMPRESS = 1;

struct _TempData {
    std::vector<uint8_t> buffer;
    std::string out_buffer;
};

struct libpf_SnappyFd {
    PyObject_HEAD
    FILE *fp;
    int mode;

    // Temp data
    _TempData *td;
};

extern PyTypeObject libpf_SnappyFdType;
