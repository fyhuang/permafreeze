#include <Python.h>

#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>

#include "libpf.h"

// Blake data structures
extern "C" {
    typedef struct
    {
    uint64_t h[8], s[4], t[2];
    int buflen, nullt;
    uint8_t buf[128];
    } state512;

    void blake512_init( state512 *S );
    void blake512_update( state512 *S, const uint8_t *in, uint64_t inlen );
    void blake512_final( state512 *S, uint8_t *out );
}

#define READ_SIZE (1024*64)
#define NUM_HASH_BITS (512)
#define NUM_HASH_BYTES (NUM_HASH_BITS / 8)

/* Benchmark results (38MB file)
 *
 * keccak, mmap: 7.21s
 * keccak, read: 7.48s
 * blake,  read: 0.287s
 */

static PyObject *
libpf_hash_and_size(PyObject *self, PyObject *args) {
    const char *filename;

    if (!PyArg_ParseTuple(args, "es", "utf8", &filename)) {
        return NULL;
    }

    state512 state;
    blake512_init(&state);


    uint8_t buffer[READ_SIZE];
    FILE *fp = fopen(filename, "rb");
    if (fp == NULL) {
        char errbuf[256];
        snprintf(errbuf, 256, "couldn't open file %s", filename);
        PyErr_SetString(PyExc_IOError, errbuf);
        return NULL;
    }

    while (!feof(fp)) {
        size_t read_bytes = fread(buffer, 1, READ_SIZE, fp);
        blake512_update(&state, buffer, read_bytes);
    }

    Py_ssize_t file_size = ftell(fp);
    fclose(fp);


    uint8_t hash[NUM_HASH_BYTES];
    blake512_final(&state, hash);

    // Convert hash to ASCII
    char hash_asc[NUM_HASH_BYTES*2+2];
    hash_asc[0] = 'F';
    size_t off = 1;
    for (int i = 0; i < NUM_HASH_BYTES; i++) {
        sprintf(hash_asc+off, "%02x", hash[i]);
        off += 2;
    }

    if (off != NUM_HASH_BYTES*2) {
        PyErr_SetString(PyExc_RuntimeError, "wrong offset");
        return NULL;
    }

    return Py_BuildValue("s#n", (char *)(&hash_asc[0]), NUM_HASH_BYTES*2, file_size);
}


static PyMethodDef LibpfMethods[] = {
    {"hash_and_size", libpf_hash_and_size, METH_VARARGS, "Return the hash of a file's contents and its size in bytes"},
    {NULL, NULL, 0, NULL}
};

extern "C" {
    PyMODINIT_FUNC inithasher(void);
}

PyMODINIT_FUNC
initlibpf()
{
    if (PyType_Ready(&libpf_SnappyFdType) < 0)
        return;

    PyObject *m = Py_InitModule3("libpf", LibpfMethods, "Native helpers for permafreeze");
    if (m == NULL)
        return;

    PyModule_AddObject(m, "KEY_NUM_CHARS",
            Py_BuildValue("i", NUM_HASH_BYTES*2));
    PyModule_AddObject(m, "MODE_COMPRESS",
            Py_BuildValue("i", MODE_COMPRESS));
    PyModule_AddObject(m, "MODE_DECOMPRESS",
            Py_BuildValue("i", MODE_DECOMPRESS));

    Py_INCREF(&libpf_SnappyFdType);
    PyModule_AddObject(m, "SnappyFd",
            (PyObject *)&libpf_SnappyFdType);
}
