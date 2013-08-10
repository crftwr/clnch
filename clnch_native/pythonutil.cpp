#include "strutil.h"
#include "pythonutil.h"

bool PythonUtil::PyStringToString( const PyObject * pystr, std::string * str )
{
	if( PyUnicode_Check(pystr) )
	{
		*str = StringUtil::WideCharToMultiByte( (const wchar_t*)PyUnicode_AS_UNICODE(pystr), PyUnicode_GET_SIZE(pystr) );
		return true;
	}
	else
	{
		PyErr_SetString( PyExc_TypeError, "must be string or unicode." );
		*str = "";
		return false;
	}
}

bool PythonUtil::PyStringToWideString( const PyObject * pystr, std::wstring * str )
{
	if( PyUnicode_Check(pystr) )
	{
		*str = (wchar_t*)PyUnicode_AS_UNICODE(pystr);
		return true;
	}
	else
	{
		PyErr_SetString( PyExc_TypeError, "must be string or unicode." );
		*str = L"";
		return false;
	}
}
