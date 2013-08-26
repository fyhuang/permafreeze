#include <Python.h>

#include <stdint.h>
#include "snappy.h"
#include "crc32c.h"

#include "libpf.h"

//#define SNAPPYFD_EXT_FORMAT
#ifndef SNAPPYFD_EXT_FORMAT
typedef uint8_t chunkid_t;
typedef int chunkret_t;
typedef uint16_t chunklen_t;
typedef crc_t csum_t;

const size_t _max_uncompressed_bytes = 32768;

#else
// TODO
#endif

#define CRC_MASK(x) ( (((x) >> 15) | ((x) << 17)) + 0xa282ead8)

const char *_snappy_magic = "sNaPpY";
const float _max_comp_ratio = 0.98f;


float _compress(libpf_SnappyFd *self) {
    // Returns compression ratio (compressed size / raw size)
    snappy::Compress((const char *)&self->td->buffer[0],
            self->td->buffer.size(),
            &self->td->out_buffer);

    float ratio = (float)(self->td->out_buffer.size()) /
        self->td->buffer.size();
    return ratio;
}

bool _decompress(libpf_SnappyFd *self) {
    // Returns length of uncompressed data
    bool success = snappy::Uncompress((const char *)&self->td->buffer[0],
            self->td->buffer.size(),
            &self->td->out_buffer);

    return success;
}

void _writeChunk(libpf_SnappyFd *self, chunkid_t chunkid, chunklen_t data_len, const uint8_t *data) {
    csum_t csum = 0;
    chunklen_t len = data_len;

    if (chunkid == 0x00 || chunkid == 0x01) {
        data_len += sizeof(csum_t);

        // Compute CRC
        csum = crc_init();
        csum = crc_update(csum, data, data_len);
        csum = crc_finalize(csum);
        csum = CRC_MASK(csum);
    }

    fwrite(&chunkid, sizeof(chunkid_t), 1, self->fp);
    fwrite(&len, sizeof(chunklen_t), 1, self->fp);

    if (chunkid == 0x00 || chunkid == 0x01) {
        fwrite(&csum, sizeof(csum_t), 1, self->fp);
    }

    fwrite(data, data_len, 1, self->fp);

    printf("Wrote chunk (len %u)\n", len);
}

chunkret_t _readChunk(libpf_SnappyFd *self) {
    const size_t hdr_size = sizeof(chunkid_t) + sizeof(chunklen_t);
    uint8_t header[hdr_size];

    size_t bytes_read = fread(header, hdr_size, 1, self->fp);
    if (bytes_read < hdr_size) {
        return -1; // Error or EOF
    }

    chunkid_t cid = *((chunkid_t*)header);
    chunklen_t len = *((chunklen_t*)(header+sizeof(chunkid_t)));

    // Read data
    self->td->buffer.resize(len);
    bytes_read = fread(&self->td->buffer[0], len, 1, self->fp);
    if (bytes_read < len) {
        return -1;
    }

    if (cid == 0x00 || cid == 0x01) {
        csum_t stored_csum = *((csum_t*)&self->td->buffer[0]);
        // Compute checksum
        csum_t csum = crc_init();
        csum = crc_update(csum,
                &self->td->buffer[sizeof(csum_t)],
                len - sizeof(csum_t));
        csum = crc_finalize(csum);
        csum = CRC_MASK(csum);

        if (csum != stored_csum) {
            return -2; // Checksum mismatch
        }

        // Decompress
        if (cid == 0x00) {
            bool success = _decompress(self);
            return success ? cid : -1;
        }
    }

    return cid;
}

void _close(libpf_SnappyFd *self) {
    if (self->fp) {
        // TODO: flush buffers
        fflush(self->fp);
        fclose(self->fp);
    }
    self->fp = NULL;
    self->mode = -1;
}


static PyObject *SnappyFd_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
    libpf_SnappyFd *self;

    self = (libpf_SnappyFd *)type->tp_alloc(type, 0);
    if (self != NULL) {
        self->fp = NULL;
        self->mode = -1;

        self->td = new _TempData;
        if (self->td == NULL) {
            Py_DECREF(self);
            return NULL;
        }
    }

    return (PyObject *)self;
}

static void SnappyFd_dealloc(libpf_SnappyFd *self) {
    if (self->fp) {
        _close(self);
    }

    if (self->td) {
        delete self->td;
        self->td = NULL;
    }

    self->ob_type->tp_free((PyObject *)self);
}

static PyObject *SnappyFd_close(libpf_SnappyFd *self) {
    _close(self);
    Py_RETURN_NONE;
}

static int SnappyFd_init(libpf_SnappyFd *self, PyObject *args, PyObject *kwargs) {
    int mode;
    const char *filename;

    if (!PyArg_ParseTuple(args, "esi", "utf8", &filename, &mode)) {
        return -1;
    }

    if (self->fp != NULL) {
        _close(self);
    }

    self->mode = mode;
    if (mode == MODE_COMPRESS) {
        self->fp = fopen(filename, "wb");
        // Write stream ID chunk
        _writeChunk(self, 0xff, 6, (const uint8_t *)_snappy_magic);
    }
    else if (mode == MODE_DECOMPRESS) {
        self->fp = fopen(filename, "rb");
        chunkret_t cret = _readChunk(self);
        if (cret != 0xff) {
            PyErr_SetString(PyExc_IOError, "first chunk ID not 0xff");
            return -1;
        }

        if (self->td->buffer.size() != 6 ||
                strcmp((const char *)&self->td->buffer[0],
                    _snappy_magic) != 0) {
            PyErr_SetString(PyExc_IOError, "wrong magic string");
            return -1;
        }
    }
    else {
        PyErr_SetString(PyExc_ValueError, "invalid mode");
        return -1;
    }

    // TODO: setup buffers

    return 0;
}

static PyObject *SnappyFd_write(libpf_SnappyFd *self, PyObject *args) {
    Py_buffer buf;

    //if (!PyArg_ParseTuple(args, "y*", ...))
    if (!PyArg_ParseTuple(args, "s*", &buf)) {
        return NULL;
    }

    int chunks = DIV_RNDUP(buf.len, _max_uncompressed_bytes);
    printf("Writing %d chunks\n", chunks);

    for (int i = 0; i < chunks; i++) {
        // copy to buffer
        size_t off = i * _max_uncompressed_bytes;
        size_t clen = (i == chunks-1) ?
            (buf.len % _max_uncompressed_bytes) :
            _max_uncompressed_bytes;
        assert(clen > 0);
        self->td->buffer.resize(clen);
        memcpy(&(self->td->buffer[0]), (uint8_t*)buf.buf + off, clen);

        float cratio = _compress(self);

        if (cratio > _max_comp_ratio) {
            // Store uncompressed
            _writeChunk(self, 0x01, clen, &self->td->buffer[0]);
        }
        else {
            // Store compressed
            _writeChunk(self, 0x00,
                    self->td->out_buffer.size(),
                    (const uint8_t *)self->td->out_buffer.data());
        }
    }

    PyBuffer_Release(&buf);
    return Py_BuildValue("n", buf.len);
}


static PyMethodDef SnappyFd_methods[] = {
    {"close", (PyCFunction)SnappyFd_close, METH_NOARGS,
        "Close the Snappy file"},
    {"write", (PyCFunction)SnappyFd_write, METH_VARARGS,
        "Write data"},
    {NULL}
};

PyTypeObject libpf_SnappyFdType  = {
    PyObject_HEAD_INIT(NULL)
    0,
    "libpf.SnappyFd",
    sizeof(libpf_SnappyFd),
    0,
    (destructor)SnappyFd_dealloc, // tp_dealloc
    0, // tp_print
    0,
    0,
    0, // tp_compare
    0,
    0, // tp_as_number
    0,
    0,
    0, // tp_hash
    0,
    0, // tp_str
    0,
    0,
    0,
    Py_TPFLAGS_DEFAULT,
    "Snappy file object",
    0, // tp_traverse
    0, // tp_clear
    0, // tp_richcompare
    0, // tp_weaklistoffset
    0, // tp_iter
    0,
    SnappyFd_methods,
    0, // tp_members
    0,
    0,
    0, // tp_dict
    0,
    0,
    0, // tp_dictoffset
    (initproc)SnappyFd_init,
    0, // tp_alloc
    SnappyFd_new,
};
