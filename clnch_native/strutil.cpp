#include <windows.h>
#include "strutil.h"

std::wstring StringUtil::MultiByteToWideChar( const char * str, int len )
{
	int buf_size = len+2;
	wchar_t * buf = new wchar_t[ buf_size ];
	int write_len = ::MultiByteToWideChar( 0, 0, str, len, buf, buf_size );
	buf[write_len] = '\0';

	std::wstring ret = buf;

	delete [] buf;

	return ret;
}

std::string StringUtil::WideCharToMultiByte( const wchar_t * str, int len )
{
	int buf_size = len*2+2;
	char * buf = new char[ buf_size ];
	int write_len = ::WideCharToMultiByte( 0, 0, str, len, buf, buf_size, NULL, NULL );
	buf[write_len] = '\0';

	std::string ret = buf;

	delete [] buf;

	return ret;
}

