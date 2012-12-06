#include <Python.h>

#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include "keccak/KeccakNISTInterface.h"

#define READ_SIZE 1024*64
#define NUM_HASH_BITS 256
#define NUM_HASH_BYTES (NUM_HASH_BITS / 8)
#define NUM_SIZE_BYTES sizeof(uint64_t)

static PyObject *
hasher_file_unique_key(PyObject *self, PyObject *args) {
    const char *filename;

    if (!PyArg_ParseTuple(args, "es", "utf8", &filename)) {
        return NULL;
    }

    hashState state;
    if (Init(&state, NUM_HASH_BITS) != SUCCESS) {
        fprintf(stderr, "hasher: couldn't initialize Keccak\n");
        PyErr_SetString(PyExc_RuntimeError, "couldn't initialize Keccak");
        return NULL;
    }

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
        HashReturn result = Update(&state, buffer, read_bytes*8);
        if (result != SUCCESS) {
            fprintf(stderr, "hasher: couldn't absorb data\n");
            PyErr_SetString(PyExc_RuntimeError, "couldn't absorb data");
            fclose(fp);
            return NULL;
        }
    }

    uint64_t file_size = ftell(fp);
    fclose(fp);

    uint8_t hash[NUM_HASH_BYTES];
    if (Final(&state, hash) != SUCCESS) {
        fprintf(stderr, "hasher: couldn't squeeze hash\n");
        PyErr_SetString(PyExc_RuntimeError, "couldn't squeeze hash");
        return NULL;
    }


    // Convert hash to ASCII
    char hash_asc[NUM_HASH_BYTES*2 + NUM_SIZE_BYTES*2 + 1];
    int i;
    size_t off = 0;
    for (i = 0; i < NUM_HASH_BYTES; i++) {
        sprintf(hash_asc+off, "%02x", hash[i]);
        off += 2;
    }

    // Convert size to ASCII (little-endian)
    uint8_t *fs_ptr = &file_size;
    for (i = 0; i < NUM_SIZE_BYTES; i++) {
        sprintf(hash_asc+off, "%02x", fs_ptr[i]);
        off += 2;
    }


    if (off != NUM_HASH_BYTES*2 + NUM_SIZE_BYTES*2) {
        PyErr_SetString(PyExc_RuntimeError, "wrong offset");
        return NULL;
    }

    hash_asc[off] = '\0';
    return Py_BuildValue("s", (char *)(&hash_asc[0]));
}


static PyMethodDef HasherMethods[] = {
    {"file_unique_key", hasher_file_unique_key, METH_VARARGS, "Return the unique key for a file"},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
inithasher(void) {
    PyObject *m = Py_InitModule("hasher", HasherMethods);
    if (m == NULL)
        return;

    PyModule_AddObject(m, "KEY_NUM_CHARS",
            Py_BuildValue("i", NUM_HASH_BYTES*2 + NUM_SIZE_BYTES*2)
            );
}
