#include "olednd_stgmedium.h"

BOOL CSTGMEDIUM::Dup(STGMEDIUM *pdest, const FORMATETC* pFormatetc, const STGMEDIUM *pmedium)
{
	HANDLE	hVoid;

	switch (pmedium->tymed) {
	case TYMED_HGLOBAL:
		hVoid = OleDuplicateData(pmedium->hGlobal, pFormatetc->cfFormat, (UINT)NULL);
		pdest->hGlobal = (HGLOBAL)hVoid;
		break;
	case TYMED_GDI:
		hVoid = OleDuplicateData(pmedium->hBitmap, pFormatetc->cfFormat, (UINT)NULL);
		pdest->hBitmap = (HBITMAP)hVoid;
		break;
	case TYMED_MFPICT:
		hVoid = OleDuplicateData(pmedium->hMetaFilePict, pFormatetc->cfFormat, (UINT)NULL);
		pdest->hMetaFilePict = (HMETAFILEPICT)hVoid;
		break;
	case TYMED_ENHMF:
		hVoid = OleDuplicateData(pmedium->hEnhMetaFile, pFormatetc->cfFormat, (UINT)NULL);
		pdest->hEnhMetaFile = (HENHMETAFILE)hVoid;
		break;
	case TYMED_FILE:
		hVoid = OleDuplicateData(pmedium->lpszFileName, pFormatetc->cfFormat, (UINT)NULL);
		pdest->lpszFileName = (LPOLESTR)hVoid;
		break;
	case TYMED_NULL:
		hVoid = (HANDLE)1; //ƒGƒ‰[‚É‚È‚ç‚È‚¢‚æ‚¤‚É
	case TYMED_ISTREAM:
	case TYMED_ISTORAGE:
	default:
		hVoid = NULL;
		break;
	}
	if(hVoid == NULL) return FALSE;
	pdest->tymed = pmedium->tymed;
	pdest->pUnkForRelease = pmedium->pUnkForRelease;
	if (pmedium->pUnkForRelease != NULL) pmedium->pUnkForRelease->AddRef();

	return	TRUE;
}
