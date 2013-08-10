#ifndef _PYTHONUTIL_H_
#define _PYTHONUTIL_H_

#include <string>
#include "python.h"

namespace PythonUtil
{
    bool PyStringToString( const PyObject * pystr, std::string * str );
	bool PyStringToWideString( const PyObject * pystr, std::wstring * str );
	
	//#define GIL_Ensure_TRACE printf("%s(%d) : %s\n",__FILE__,__LINE__,__FUNCTION__)
	#define GIL_Ensure_TRACE

	class GIL_Ensure
	{
	public:
		GIL_Ensure()
		{
			GIL_Ensure_TRACE;
			state = PyGILState_Ensure();
			GIL_Ensure_TRACE;
		};

		~GIL_Ensure()
		{
			GIL_Ensure_TRACE;
			PyGILState_Release(state);
			GIL_Ensure_TRACE;
		};
		
	private:
		PyGILState_STATE state;
	};
};

#endif // _PYTHONUTIL_H_
