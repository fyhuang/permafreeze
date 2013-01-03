#include <Python.h>

#include <cstdint>
#include "snappy.h"

#include "libpf.h"

//#define SNAPPYFD_EXT_FORMAT
#ifndef SNAPPYFD_EXT_FORMAT
typedef uint8_t chunkid_t;
typedef uint16_t chunklen_t;

#else
// TODO
#endif


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
        fclose(self->fp);
    }
    if (self->td) {
        delete self->td;
    }

    self->fp = NULL;
    self->mode = -1;
    self->td = NULL;

    self->ob_type->tp_free((PyObject *)self);
}

static void SnappyFd_close(libpf_SnappyFd *self) {
    if (self->fp) {
        // TODO: flush buffers
        fclose(self->fp);
    }
    self->fp = NULL;
    self->mode = -1;
}

static int SnappyFd_init(libpf_SnappyFd *self, PyObject *args, PyObject *kwargs) {
    int mode;
    const char *filename;

    if (!PyArg_ParseTyple(args, "esi", "utf8", &filename, &mode)) {
        return NULL;
    }

    if (self->fp != NULL) {
        SnappyFd_close(self);
    }

    self->mode = mode;
    if (mode == MODE_COMPRESS) {
        self->fp = fopen(filename, "wb");
        // Write stream ID chunk
        _writeChunk(0xff, 6, "sNaPpY");
    }
    else if (mode == MODE_DECOMPRESS) {
        self->fp = fopen(filename, "rb");
    }
    else {
        PyErr_SetString(PyExc_ValueError, "invalid mode");
        return NULL;
    }

    // TODO: setup buffers
}


static PyMethodDef SnappyFd_methods[] = {
    {"close", (PyCFunction)SnappyFd_close, METH_NOARGS,
        "Close the Snappy file"},
    {NULL}
};

PyTypeObject libpf_SnappyFdType  = {
    PyObject_HEAD_INIT(NULL)
    0,
    "libpf.SnappyFd",
    sizeof(libpf_SnappyFd),
    0,
    0, // tp_dealloc
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
