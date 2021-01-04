#ifndef __CSTGMEDIUM
#define __CSTGMEDIUM

#include "windows.h"

class CSTGMEDIUM {
  public:
	  static BOOL Dup(STGMEDIUM *pdest, const FORMATETC* pFormatetc, const STGMEDIUM *pmedium);
};

#endif
