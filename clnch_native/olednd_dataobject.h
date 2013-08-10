#ifndef __CDataObject
#define __CDataObject

#include "olednd_mydarray.h"
#include "olednd_enumformatetc.h"
#include "olednd_stgmedium.h"

class CDataObject : public IDataObject
{
  public:
	  CDataObject() : _RefCount(1){
		  _num = 0;
	  };
	  ~CDataObject(){};

	virtual HRESULT __stdcall QueryInterface(const IID& iid, void** ppv);
	virtual ULONG __stdcall AddRef(void);
	virtual ULONG __stdcall Release(void);

	virtual HRESULT __stdcall GetData(FORMATETC *pFormatetc, STGMEDIUM *pmedium);
	virtual HRESULT __stdcall GetDataHere(FORMATETC *pFormatetc, STGMEDIUM *pmedium);
	virtual HRESULT __stdcall QueryGetData(FORMATETC *pFormatetc);
	virtual HRESULT __stdcall GetCanonicalFormatEtc(FORMATETC *pFormatetcIn, FORMATETC *pFormatetcInOut);
	virtual HRESULT __stdcall SetData(FORMATETC *pFormatetc, STGMEDIUM *pmedium, BOOL fRelease); /*fRelease=TRUE‚ÌŽžDataObject*/
	virtual HRESULT __stdcall EnumFormatEtc(DWORD dwDirection, IEnumFORMATETC **ppenumFormatetc);
	virtual HRESULT __stdcall DAdvise(FORMATETC *pFormatetc, DWORD advf, IAdviseSink *pAdvSink, DWORD *pdwConnection);
	virtual HRESULT __stdcall DUnadvise(DWORD dwConnection);
	virtual HRESULT __stdcall EnumDAdvise(IEnumSTATDATA **ppenumAdvise);

	BOOL allocate(int num);

  protected:
	class CObject{
	public:
		FORMATETC	fmt;
		STGMEDIUM	medium;
	public:
		CObject(){
			medium.tymed = TYMED_NULL;
		}
		~CObject(){
			if(medium.tymed != TYMED_NULL) ReleaseStgMedium(&medium);
		}
		BOOL Set(FORMATETC* pf, STGMEDIUM *pm, BOOL fRelease){
			fmt = *pf;
			if(fRelease){
				medium = *pm;
				return	TRUE;
			} else{
				return CSTGMEDIUM::Dup(&medium, pf, pm);
			}
		}
	};

	typedef CMyDArray<CObject> OBJLIST;
	LONG _RefCount;
	OBJLIST	_Objects;
	int		_num;
};

#endif
