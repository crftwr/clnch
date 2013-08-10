#ifndef __CLNCH_NATIVE_H__
#define __CLNCH_NATIVE_H__


extern PyTypeObject LockFile_Type;
#define LockFile_Check(op) PyObject_TypeCheck(op, &LockFile_Type)

struct LockFile_Object
{
    PyObject_HEAD
    HANDLE handle;
};


extern PyTypeObject CheckDir_Type;
#define CheckDir_Check(op) PyObject_TypeCheck(op, &CheckDir_Type)

struct CheckDir_Object
{
    PyObject_HEAD
    class CheckDir * p;
};


#endif /* __CLNCH_NATIVE_H__ */
