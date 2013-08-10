#ifndef _STRUTIL_H_
#define _STRUTIL_H_

#include <string>

namespace StringUtil
{
	std::wstring MultiByteToWideChar( const char * str, int len );
	std::string WideCharToMultiByte( const wchar_t * str, int len );
};

#endif // _STRUTIL_H_
