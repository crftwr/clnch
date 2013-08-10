#include "olednd_dataobject.h"

HRESULT __stdcall CDataObject::QueryInterface(const IID& iid, void** ppv)
{
	HRESULT hr;

	if(iid == IID_IDataObject || iid == IID_IUnknown){
		hr = S_OK;
		*ppv = (void*)this;
		AddRef();
	}else{
		hr = E_NOINTERFACE;
		*ppv = 0;
	}
	return hr;
}


ULONG __stdcall CDataObject::AddRef()
{
	InterlockedIncrement(&_RefCount);
	return (ULONG)_RefCount;
}


ULONG __stdcall CDataObject::Release()
{
	ULONG ret = (ULONG)InterlockedDecrement(&_RefCount);
	if(ret == 0){
		delete this;
	}
	return (ULONG)_RefCount;
}

HRESULT __stdcall CDataObject::GetData(FORMATETC *pFormatetc, STGMEDIUM *pmedium)
{
	int	i;

	if(pFormatetc == NULL || pmedium == NULL){
		return E_INVALIDARG;
	}

	if (!(DVASPECT_CONTENT & pFormatetc->dwAspect)) return DV_E_DVASPECT;

	for(i = 0; i < _num; ++i){
		if(_Objects[i].fmt.cfFormat == pFormatetc->cfFormat && 
			(_Objects[i].fmt.tymed & pFormatetc->tymed) != 0){
			if(CSTGMEDIUM::Dup(pmedium, &_Objects[i].fmt, &_Objects[i].medium) == FALSE){
				return E_OUTOFMEMORY;
			}
			return S_OK;
		}
	}

	return DV_E_FORMATETC;
}

// GetData‚Æ“¯‚¶‚æ‚¤‚È‚à‚Ì‚ç‚µ‚¢‚ª‚æ‚­•ª‚©‚ç‚È‚¢
HRESULT __stdcall CDataObject::GetDataHere(FORMATETC *pFormatetc, STGMEDIUM *pmedium)
{
	return E_NOTIMPL;
}


HRESULT __stdcall CDataObject::QueryGetData(FORMATETC *pFormatetc)
{
	int	i;

	if(pFormatetc == NULL){
		return E_INVALIDARG;
	}

	if (!(DVASPECT_CONTENT & pFormatetc->dwAspect)) return DV_E_DVASPECT;

	for(i = 0; i < _num; ++i){
		if(_Objects[i].fmt.cfFormat == pFormatetc->cfFormat && 
			(_Objects[i].fmt.tymed & pFormatetc->tymed) != 0){
			return S_OK;
		}
	}

	return DV_E_FORMATETC;
}

HRESULT __stdcall CDataObject::EnumFormatEtc(DWORD dwDirection, IEnumFORMATETC **ppenumFormatetc)
{
	int	i;
	CEnumFORMATETC*	pfmt;

	if (ppenumFormatetc == NULL){
		return E_INVALIDARG;
	}
	
	*ppenumFormatetc = NULL;
	switch (dwDirection) {
		case DATADIR_GET:
			pfmt = new CEnumFORMATETC;
			if(pfmt == NULL){
				return E_OUTOFMEMORY;
			}
			
			if(!pfmt->allocate(_Objects.size())){
				delete pfmt;
				return E_OUTOFMEMORY;
			}

			for(i = 0; i < _num; ++i){
				pfmt->SetFormat(&_Objects[i].fmt);
			}
			*ppenumFormatetc = pfmt;
			break;
		default:
			return E_NOTIMPL;
	}

	return S_OK;
}

HRESULT __stdcall CDataObject::SetData(FORMATETC *pFormatetc, STGMEDIUM *pmedium, BOOL fRelease)
{
	if(pFormatetc == NULL || pmedium == NULL) return E_INVALIDARG;

	if(_num >= _Objects.size()) return E_OUTOFMEMORY;

	if(_Objects[_num].Set(pFormatetc, pmedium, fRelease) == FALSE) return E_OUTOFMEMORY;

	_num++;

	return S_OK;
}


HRESULT __stdcall CDataObject::GetCanonicalFormatEtc(FORMATETC *pFormatetcIn, FORMATETC *pFormatetcOut)
{
	return E_NOTIMPL;
}

HRESULT __stdcall CDataObject::DAdvise(FORMATETC *pFormatetc, DWORD advf, IAdviseSink *pAdvSink, DWORD *pdwConnection)
{
	return OLE_E_ADVISENOTSUPPORTED;
}

HRESULT __stdcall CDataObject::DUnadvise(DWORD dwConnection)
{
	return OLE_E_ADVISENOTSUPPORTED;
}

HRESULT __stdcall CDataObject::EnumDAdvise(IEnumSTATDATA **ppenumAdvise)
{
	return OLE_E_ADVISENOTSUPPORTED;
}

BOOL CDataObject::allocate(int num)
{
	return	_Objects.allocate(num);
}
