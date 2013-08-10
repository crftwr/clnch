#ifndef __CDropSource
#define __CDropSource

#include <shlobj.h>

class CDropSource : public IDropSource
{
public:
	CDropSource() : _RefCount(1){};
	~CDropSource(){};

	virtual HRESULT __stdcall QueryInterface(const IID& iid, void** ppv);
	virtual ULONG __stdcall AddRef(void);
	virtual ULONG __stdcall Release(void);

	virtual HRESULT __stdcall QueryContinueDrag(BOOL fEscapePressed, DWORD grfKeyState);
	virtual HRESULT __stdcall GiveFeedback(DWORD dwEffect);

private:
	LONG _RefCount;
};

#endif
