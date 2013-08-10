#ifndef __CEnumFORMATETC
#define __CEnumFORMATETC

#include "olednd_mydarray.h"

class CEnumFORMATETC : public IEnumFORMATETC
{
  public:
	  CEnumFORMATETC() : _RefCount(1){
		  _current = 0;
		  _num = 0;
	  };
	  ~CEnumFORMATETC(){};

	virtual HRESULT __stdcall QueryInterface(const IID& iid, void** ppv);
	virtual ULONG __stdcall AddRef(void);
	virtual ULONG __stdcall Release(void);

	virtual HRESULT __stdcall Next(ULONG celt, FORMATETC * rgelt, ULONG * pceltFetched);
	virtual HRESULT __stdcall Skip(ULONG celt);
	virtual HRESULT __stdcall Reset(void);
	virtual HRESULT __stdcall Clone(IEnumFORMATETC ** ppenum);

	BOOL allocate(int num);
	BOOL SetFormat(FORMATETC *fmt);
  private:
	LONG _RefCount;
  protected:
	class CData{
	public:
		FORMATETC	fmt;
	};

	typedef	CMyDArray<CData>	FMTLIST;
	FMTLIST _fmt;
	int		_current, _num;
};

#endif
