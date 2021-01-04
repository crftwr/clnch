#include "olednd_enumformatetc.h"

HRESULT __stdcall CEnumFORMATETC::QueryInterface(const IID& iid, void** ppv)
{
	HRESULT hr;

	if(iid == IID_IEnumFORMATETC || iid == IID_IUnknown){
		hr = S_OK;
		*ppv = (void*)this;
		AddRef();
	}else{
		hr = E_NOINTERFACE;
		*ppv = 0;
	}
	return hr;
}


ULONG __stdcall CEnumFORMATETC::AddRef()
{
	InterlockedIncrement(&_RefCount);
	return (ULONG)_RefCount;
}


ULONG __stdcall CEnumFORMATETC::Release()
{
	ULONG ret = (ULONG)InterlockedDecrement(&_RefCount);
	if(ret == 0){
		delete this;
	}
	return (ULONG)_RefCount;
}

HRESULT __stdcall CEnumFORMATETC::Next(ULONG celt, FORMATETC * rgelt, ULONG * pceltFetched)
{
	ULONG n = celt;
	
	if(pceltFetched != NULL) *pceltFetched = 0;
	
	if(celt <= 0 || rgelt == NULL || _current >= _num)	return S_FALSE;
	
	/* celtが1の時だけpceltFetchedはNULLに出来る*/
	if(pceltFetched == NULL && celt != 1)	return S_FALSE;
	
	while(_current < _num && n > 0) {
		*rgelt++ = _fmt[_current].fmt;
		++_current;
		--n;
	}
	if(pceltFetched != NULL) *pceltFetched = celt - n;
	
	return (n == 0)? S_OK : S_FALSE;
}

HRESULT __stdcall CEnumFORMATETC::Skip(ULONG celt)
{

	while(_current < _num && celt > 0) {
		++_current;
		--celt;
	}

	return (celt == 0)? S_OK : S_FALSE;
}

HRESULT __stdcall CEnumFORMATETC::Reset(void)
{
	_current = 0;
	return S_OK;
}

HRESULT __stdcall CEnumFORMATETC::Clone(IEnumFORMATETC ** ppenum)
{
	CEnumFORMATETC	*pfmt;
	int				i;
	
	if (ppenum == NULL)	return E_POINTER;

	pfmt = new CEnumFORMATETC;
	if(pfmt == NULL) return E_OUTOFMEMORY;

	if(!pfmt->allocate(_num)){
		delete pfmt;
		return E_OUTOFMEMORY;
	}

	for(i = 0; i < _num; ++i){
		pfmt->SetFormat(&_fmt[i].fmt);
	}

	pfmt->_current = _current;
	*ppenum = pfmt;

	return S_OK;
}

BOOL CEnumFORMATETC::SetFormat(FORMATETC *fmt)
{
	FMTLIST::iterator	obj;

	if(fmt == NULL) return FALSE;

	if(_num >= _fmt.size()) return E_OUTOFMEMORY;

	_fmt[_num].fmt = *fmt;

	_num++;
	
	return	TRUE;
}

BOOL CEnumFORMATETC::allocate(int num)
{
	return	_fmt.allocate(num);
}

