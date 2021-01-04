#include "olednd_dropsource.h"

HRESULT __stdcall CDropSource::QueryInterface(const IID& iid, void** ppv)
{
	HRESULT hr;

	if(iid == IID_IDropSource || iid == IID_IUnknown){
		hr = S_OK;
		*ppv = (void*)this;
		AddRef();
	}else{
		hr = E_NOINTERFACE;
		*ppv = 0;
	}
	return hr;
}


ULONG __stdcall CDropSource::AddRef()
{
	InterlockedIncrement(&_RefCount);
	return (ULONG)_RefCount;
}


ULONG __stdcall CDropSource::Release()
{
	ULONG ret = (ULONG)InterlockedDecrement(&_RefCount);
	if(ret == 0){
		delete this;
	}
	return (ULONG)_RefCount;
}

HRESULT __stdcall CDropSource::QueryContinueDrag(BOOL fEscapePressed, DWORD grfKeyState)
{
	/* ドラッグを継続するかどうかを決める */

	/* ESCが押された場合やマウスのボタンが両方押されたときは中止 */
	if(fEscapePressed || (MK_LBUTTON | MK_RBUTTON) == (grfKeyState & (MK_LBUTTON | MK_RBUTTON))){
		return DRAGDROP_S_CANCEL;
	}

	/* マウスボタンが離されたときはドロップ */
	if((grfKeyState & (MK_LBUTTON | MK_RBUTTON)) == 0){
		return DRAGDROP_S_DROP;
	}
	return S_OK;
}

HRESULT __stdcall CDropSource::GiveFeedback(DWORD dwEffect)
{
	/* マウスカーソルを変えたり、特別な表示をするときはここで行う */

	//標準のマウスカーソルを使う
	return DRAGDROP_S_USEDEFAULTCURSORS;
}
