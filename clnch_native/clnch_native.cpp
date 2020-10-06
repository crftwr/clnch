#include <shlobj.h>
#include <intshcut.h>
#include <lm.h>

#include <vector>
#include <list>
#include <string>

#if defined(_DEBUG)
#undef _DEBUG
#include "python.h"
#define _DEBUG
#else
#include "python.h"
#endif

#include "frameobject.h"

#include "pythonutil.h"
#include "strutil.h"

#include "clnch_native.h"

//using namespace clnch;

//-----------------------------------------------------------------------------

#define MODULE_NAME "clnch_native"
static PyObject * Error;

//-----------------------------------------------------------------------------

//#define PRINTF printf
#define PRINTF(...)

//#define TRACE printf("%s(%d) : %s\n",__FILE__,__LINE__,__FUNCTION__)
#define TRACE

#if 0
	struct FuncTrace
	{
		FuncTrace( const char * _funcname, unsigned int _lineno )
		{
			funcname = _funcname;
			lineno   = _lineno;
		
			printf( "FuncTrace : Enter : %s(%)\n", funcname, lineno );
		}

		~FuncTrace()
		{
			printf( "FuncTrace : Leave : %s(%)\n", funcname, lineno );
		}
	
		const char * funcname;
		unsigned int lineno;
	};
	#define FUNC_TRACE FuncTrace functrace(__FUNCTION__,__LINE__)
#else
	#define FUNC_TRACE
#endif

// ----------------------------------------------------------------------------

struct FindFileCacheInfo
{
	std::wstring filename;
	long long filesize;
	DWORD attributes;
	SYSTEMTIME system_time;
};

typedef std::list<FindFileCacheInfo> FindFileCacheInfoList;

class FindFileCache
{
public:
	FindFileCache( const std::wstring & _path, bool _ignore_dot, bool _ignore_dotdot, FindFileCacheInfoList & _info_list )
		:
		path(_path),
		ignore_dot(_ignore_dot),
		ignore_dotdot(_ignore_dotdot),
		info_list(_info_list)
	{
	}

	FindFileCache( const FindFileCache & src )
		:
		path(src.path),
		ignore_dot(src.ignore_dot),
		ignore_dotdot(src.ignore_dotdot),
		info_list(src.info_list)
	{
	}

	~FindFileCache()
	{
	}

public:
	std::wstring path;
	bool ignore_dot;
	bool ignore_dotdot;
	FindFileCacheInfoList info_list;
};

typedef std::list<FindFileCache> FindFileCacheList;
static FindFileCacheList find_file_cache_list;

static PyObject * _findFile(PyObject* self, PyObject* args, PyObject * kwds)
{
	PyObject * pypath;
	int ignore_dot = true;
	int ignore_dotdot = true;
	int use_cache = false;

    static char * kwlist[] = {
        "path",
        "ignore_dot",
        "ignore_dotdot",
        "use_cache",
        NULL
    };
    
    if(!PyArg_ParseTupleAndKeywords( args, kwds, "O|iii", kwlist,
        &pypath,
        &ignore_dot,
        &ignore_dotdot,
        &use_cache
    ))
    {
        return NULL;
	}

	std::wstring path;
	PythonUtil::PyStringToWideString( pypath, &path );
	
	bool found = false;
	
	if(use_cache)
	{
		// キャッシュを検索する
		FindFileCacheList::iterator i;
		for( i=find_file_cache_list.begin() ; i!=find_file_cache_list.end() ; ++i )
		{
			if( i->path == path
			 && i->ignore_dot == (ignore_dot!=0) 
			 && i->ignore_dotdot == (ignore_dotdot!=0) )
			{
				break;
			}
		}

		// キャッシュから見つかった		
		if(i!=find_file_cache_list.end())
		{
			found = true;

			// 先頭に入れ替え
			if(i!=find_file_cache_list.begin())
			{
				FindFileCache cache = *i;
				find_file_cache_list.erase(i);
				find_file_cache_list.insert( find_file_cache_list.begin(), cache );
			}
		}
	}

	if(!found)
	{
		FindFileCacheInfoList new_info_list;

		HANDLE handle;
		WIN32_FIND_DATA data;

		Py_BEGIN_ALLOW_THREADS
		handle = FindFirstFile( path.c_str(), &data );
		Py_END_ALLOW_THREADS

		if(handle!=INVALID_HANDLE_VALUE)
		{
			while(true)
			{
				bool ignore = false;
		
				if( ignore_dot    && wcscmp(data.cFileName,L".")==0 ){ ignore = true; }
				if( ignore_dotdot && wcscmp(data.cFileName,L"..")==0 ){ ignore = true; }
		
				if(!ignore)
				{
					FindFileCacheInfo info;

					info.filename = data.cFileName;
					info.filesize = (((long long)data.nFileSizeHigh)<<32)+data.nFileSizeLow;
					info.attributes = data.dwFileAttributes;

					FILETIME local_file_time;
					FileTimeToLocalFileTime( &data.ftLastWriteTime, &local_file_time );
					FileTimeToSystemTime( &local_file_time, &info.system_time );

					new_info_list.push_back(info);
				}
		
				BOOL found;
				Py_BEGIN_ALLOW_THREADS
				found = FindNextFile(handle, &data);
				Py_END_ALLOW_THREADS
				if(!found) break;
			}

			Py_BEGIN_ALLOW_THREADS
			FindClose(handle);
			Py_END_ALLOW_THREADS
		}
		else if( GetLastError()==ERROR_FILE_NOT_FOUND )
		{
			// エラーにせず空のリストを返す
			SetLastError(0);
		}
		else
		{
			PyErr_SetFromWindowsErr(0);
			return NULL;
		}

		// キャッシュリストの先頭に登録する
		find_file_cache_list.push_front( FindFileCache( path, ignore_dot!=0, ignore_dotdot!=0, new_info_list ) );

		// キャッシュリストのサイズを４つに制限する
		while( find_file_cache_list.size()>4 )
		{
			find_file_cache_list.pop_back();
		}
	}

	// PythonのListに変換する
	PyObject * pyret = PyList_New(0);
	{
		// キャッシュ中の先頭のアイテムを返す
		FindFileCacheInfoList & info_list = find_file_cache_list.begin()->info_list;

		for( FindFileCacheInfoList::iterator i=info_list.begin() ; i!=info_list.end() ; ++i )
		{
			PyObject * pyitem = Py_BuildValue(
				"(uL(iiiiii)i)",
				i->filename.c_str(),
				i->filesize,
				i->system_time.wYear, i->system_time.wMonth, i->system_time.wDay,
				i->system_time.wHour, i->system_time.wMinute, i->system_time.wSecond,
				i->attributes
			);

			PyList_Append( pyret, pyitem );

			Py_XDECREF(pyitem);
		}
	}

	return pyret;
}

static PyObject * _enumShare(PyObject* self, PyObject* args, PyObject * kwds)
{
	PyObject * pyservername;

    static char * kwlist[] = {
        "servername",
        NULL
    };

    if(!PyArg_ParseTupleAndKeywords( args, kwds, "O", kwlist,
        &pyservername
    ))
    {
        return NULL;
	}

	std::wstring servername;
	PythonUtil::PyStringToWideString( pyservername, &servername );

	PyObject * pyret = PyList_New(0);

	NET_API_STATUS res;
   	PSHARE_INFO_502 BufPtr, p;
   	DWORD er=0, tr=0, resume=0;   	
   	
   	do
   	{
		Py_BEGIN_ALLOW_THREADS
		res = NetShareEnum( (wchar_t*)servername.c_str(), 502, (LPBYTE *)&BufPtr, MAX_PREFERRED_LENGTH, &er, &tr, &resume );
		Py_END_ALLOW_THREADS

      	if( res==ERROR_SUCCESS || res==ERROR_MORE_DATA )
      	{
         	p=BufPtr;

         	for( unsigned int i=1 ; i<=er ; i++ )
         	{
         		/*
            	printf("%-20S%-30S%-8u",p->shi502_netname, p->shi502_path, p->shi502_current_uses);

	            // shi502_security_descriptor メンバの値が有効かどうか検証する。
	            if(IsValidSecurityDescriptor(p->shi502_security_descriptor))
	            {
	               	printf("Yes\n");
	            }
	            else
	            {
	               	printf("No\n");
	            }
	            */

				// リストに追加
				{
					PyObject * pyitem = Py_BuildValue(
						"(uiuiiiuu)",
						p->shi502_netname,
						p->shi502_type,
						p->shi502_remark,
						p->shi502_permissions,
						p->shi502_max_uses,
						p->shi502_current_uses,
						p->shi502_path,
						p->shi502_passwd
					);
				
					PyList_Append( pyret, pyitem );

					Py_XDECREF(pyitem);
				}

	            p++;
			}

        	// 割り当て済みのバッファを解放する。
        	NetApiBufferFree(BufPtr);
      	}
      	else
      	{
			Py_XDECREF(pyret);
	
			PyErr_SetFromWindowsErr(res);
			return NULL;
      	}
   	}
   	while(res==ERROR_MORE_DATA);

	return pyret;
}

static PyObject * _addConnection(PyObject* self, PyObject* args, PyObject * kwds)
{
	HWND hwnd;
	PyObject * pyservername;

    static char * kwlist[] = {
    	"hwnd",
        "servername",
        NULL
    };

    if(!PyArg_ParseTupleAndKeywords( args, kwds, "iO", kwlist,
    	&hwnd,
        &pyservername
    ))
    {
        return NULL;
	}

	std::wstring servername;
	PythonUtil::PyStringToWideString( pyservername, &servername );

	NETRESOURCE resource;
	resource.dwType = RESOURCETYPE_ANY;
	resource.lpLocalName = 0;
	resource.lpRemoteName = (wchar_t*)servername.c_str();
	resource.lpProvider = 0;

	DWORD ret = WNetAddConnection3( hwnd, &resource, 0, 0, CONNECT_INTERACTIVE );
	
	if(ret)
	{
		PyErr_SetFromWindowsErr(ret);
		return NULL;
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject * _setFileTime(PyObject* self, PyObject* args, PyObject * kwds)
{
	PyObject * pypath;
	int year, month, day, hour, minute, second;

    if( ! PyArg_ParseTuple( args, "O(iiiiii)", &pypath, &year, &month, &day, &hour, &minute, &second ) )
        return NULL;

	std::wstring path;
	PythonUtil::PyStringToWideString( pypath, &path );
	
	DWORD attr = GetFileAttributes(path.c_str());
	if(attr==-1)
	{
		PyErr_SetString( PyExc_IOError, "could not get file attribute." );
		return NULL;
	}
	
    bool is_dir = (attr&FILE_ATTRIBUTE_DIRECTORY)!=0;
    bool is_readonly = (attr&FILE_ATTRIBUTE_READONLY)!=0;
    
    if(is_readonly)
    {
    	// ReadOnly 属性のときはいったん解除しないとタイムスタンプが更新できない
		SetFileAttributes( path.c_str(), attr & (~FILE_ATTRIBUTE_READONLY) );
    }
	
	HANDLE hFile = CreateFile(
		path.c_str(), GENERIC_WRITE, 0, NULL,
		OPEN_EXISTING, is_dir?(FILE_ATTRIBUTE_NORMAL|FILE_FLAG_BACKUP_SEMANTICS):FILE_ATTRIBUTE_NORMAL, NULL
	);

	if(hFile==INVALID_HANDLE_VALUE)
	{
		PyErr_SetString( PyExc_IOError, "could not open file." );

	    if(is_readonly)
	    {
	    	// ReadOnly 属性を元に戻す
			SetFileAttributes( path.c_str(), attr );
	    }

		return NULL;
	}

	SYSTEMTIME stFileTime;
	memset( &stFileTime, 0, sizeof(stFileTime) );
	stFileTime.wYear = year;
	stFileTime.wMonth = month;
	stFileTime.wDay = day;
	stFileTime.wHour = hour;
	stFileTime.wMinute = minute;
	stFileTime.wSecond = second;
	
	FILETIME ftFileTime;
	SystemTimeToFileTime(&stFileTime, &ftFileTime);

	FILETIME ftFileTimeUTC;
	LocalFileTimeToFileTime( &ftFileTime, &ftFileTimeUTC );

	SetFileTime( hFile, NULL, NULL, &ftFileTimeUTC );

	CloseHandle(hFile);

    if(is_readonly)
    {
    	// ReadOnly 属性を元に戻す
		SetFileAttributes( path.c_str(), attr );
    }

	Py_INCREF(Py_None);
	return Py_None;
}

static LPCONTEXTMENU3 context_menu_interface3;
static WNDPROC context_menu_oldWndProc;

static LPITEMIDLIST getItemIDList( HWND hwnd, LPSHELLFOLDER pDesktopFolder, const wchar_t * filename )
{
	FUNC_TRACE;

  	LPITEMIDLIST  pidl = NULL;
	ULONG         chEaten;
	ULONG         dwAttributes;
	HRESULT       ret;

	wchar_t buf[MAX_PATH];
	wcscpy_s( buf, MAX_PATH, filename );

	ret = pDesktopFolder->ParseDisplayName(
		hwnd,
		NULL,
		buf,
		&chEaten,
		&pidl,
		&dwAttributes);

	if(FAILED(ret))
	{
		printf( "ParseDisplayName failed\n" );
		return NULL;
	}
	
	//wprintf( L"getItemIDList : %d : %s : %p\n", chEaten, buf, pidl );

  	return pidl;
}

static LRESULT CALLBACK contextMenuWndProc( HWND hwnd, UINT msg, WPARAM wp, LPARAM lp )
{
	PythonUtil::GIL_Ensure gil_ensure;

	switch(msg)
	{ 
	case WM_MENUCHAR:	// only supported by IContextMenu3
		//printf("WM_MENUCHAR\n");
		if(context_menu_interface3)
		{
			LRESULT result = 0;
			HRESULT ret = context_menu_interface3->HandleMenuMsg2( msg, wp, lp, &result );
			//printf("ret=%x result=%x\n",ret,result);
			return result;
		}
		break;

	case WM_DRAWITEM:
	case WM_MEASUREITEM:
		/*
		if(msg==WM_DRAWITEM)
		{
			printf("WM_DRAWITEM\n");
		}
		else
		{
			printf("WM_MEASUREITEM\n");
		}
		*/
		if(wp)
		{
			break; // if wParam != 0 then the message is not menu-related
		}
		// fall through
		
	case WM_INITMENUPOPUP:
		/*
		if(msg==WM_INITMENUPOPUP)
		{
			printf("WM_INITMENUPOPUP\n");
		}
		*/
		if(context_menu_interface3)
		{
			HRESULT ret = context_menu_interface3->HandleMenuMsg( msg, wp, lp );
			//printf("ret=%x\n",ret);
		}
		return (msg==WM_INITMENUPOPUP ? 0 : TRUE); // inform caller that we handled WM_INITPOPUPMENU by ourself

	default:
		break;
	}

	// call original WndProc of window to prevent undefined bevhaviour of window
	return ::CallWindowProc( context_menu_oldWndProc, hwnd, msg, wp, lp );
}

BOOL doContextMenu( HWND hwnd, int x, int y, LPSHELLFOLDER pFolder, LPITEMIDLIST * lpIDLArray, int num )
{
	FUNC_TRACE;

    LPCONTEXTMENU lpcm;
    HRESULT       ret;
    CMINVOKECOMMANDINFO cmi;
    DWORD               dwAttribs=0;
    int                 idCmd;
    HMENU               hMenu;
    BOOL                bSuccess=FALSE;

	
	#if 0

	// エクスプローラのビューの背景部分のコンテキストメニューのテスト
	// なぜか、貼り付け、が無効化されている
	IShellView * pView;
	pFolder->CreateViewObject( hwnd, IID_IShellView, (LPVOID *)&pView );
	pView->GetItemObject( SVGIO_BACKGROUND, IID_IContextMenu, (LPVOID *)&lpcm );
	pView->Release();

	#else

    //IContextMenuを取得します。
    //第三引数に、ファイルの数
    //第四引数に、ファイルのアイテムＩＤリスト配列のアドレスをいれます。
    ret = pFolder->GetUIObjectOf(
    	hwnd,
        num,
        (LPCITEMIDLIST*)lpIDLArray,
        IID_IContextMenu,
        0,
        (LPVOID *)&lpcm);
	
	#endif

	TRACE;
	
	if(ret)
	{
		return FALSE;
	}
	
	PRINTF("ret=%d\n",ret);
	PRINTF("num=%d\n",num);
	PRINTF("lpIDLArray=%p\n",lpIDLArray);
	PRINTF("lpcm=%p\n", lpcm);

    ret = lpcm->QueryInterface( IID_IContextMenu3, (void**)&context_menu_interface3 );

	TRACE;

    if(SUCCEEDED(ret))
    {
		TRACE;

        hMenu = CreatePopupMenu();

        if(hMenu)
        {
			TRACE;
        
            ret = context_menu_interface3->QueryContextMenu(
            	hMenu,
                0,
                1,
                10000,
                CMF_NORMAL | CMF_EXPLORE );

			TRACE;

            if (SUCCEEDED(ret))
            {
				TRACE;

				context_menu_oldWndProc = (WNDPROC)SetWindowLongPtr( hwnd, GWLP_WNDPROC, (LONG_PTR)contextMenuWndProc );

                bSuccess = TRUE;
                idCmd = TrackPopupMenu(hMenu, 
                                    TPM_LEFTALIGN | TPM_RETURNCMD | TPM_RIGHTBUTTON, 
                                    x, 
                                    y,
                                    0,
                                    hwnd,
                                    NULL);

				TRACE;

				SetWindowLongPtr( hwnd, GWLP_WNDPROC, (LONG_PTR)context_menu_oldWndProc);
				context_menu_oldWndProc = NULL;

                if(idCmd)
                {
					TRACE;

                    cmi.cbSize = sizeof(CMINVOKECOMMANDINFO);
                    cmi.fMask  = 0;
                    cmi.hwnd   = hwnd;
                    cmi.lpVerb = (const char*)MAKEINTRESOURCE(idCmd-1);
                    cmi.lpParameters = NULL;
                    cmi.lpDirectory  = NULL;
                    cmi.nShow        = SW_SHOWNORMAL;
                    cmi.dwHotKey     = 0;
                    cmi.hIcon        = NULL;

                    ret = context_menu_interface3->InvokeCommand(&cmi);
                    if(!SUCCEEDED(ret)) bSuccess=FALSE;
                }
            }
    
            DestroyMenu(hMenu);
        }

    	context_menu_interface3->Release();
    	context_menu_interface3 = NULL;
    	
        lpcm->Release();
    }

	TRACE;

    return bSuccess;
}

static PyObject * _popupContextMenu(PyObject* self, PyObject* args)
{
	FUNC_TRACE;

	HWND hwnd;
	int x;
	int y;
	PyObject * pystr_directory;
	PyObject * file_list;

    if( ! PyArg_ParseTuple( args, "iiiOO", &hwnd, &x, &y, &pystr_directory, &file_list ) )
        return NULL;
    
    std::wstring str_directory;
    if( !PythonUtil::PyStringToWideString( pystr_directory, &str_directory ) )
    {
    	return NULL;
    }
		
	if( !PyTuple_Check(file_list) && !PyList_Check(file_list) )
	{
		PyErr_SetString( PyExc_TypeError, "argument must be a tuple or list." );
		return NULL;
	}
	
	{
		HRESULT ret;
		LPMALLOC pMalloc;
	    LPSHELLFOLDER pDesktopFolder;
		LPITEMIDLIST directory_item_id;
	    LPSHELLFOLDER pFolder;

	    Py_BEGIN_ALLOW_THREADS

		ret = SHGetMalloc( &pMalloc );
		if(ret)
		{
			printf("SHGetMalloc failed\n");
		}

		ret = SHGetDesktopFolder(&pDesktopFolder);
		if(ret)
		{
			printf("SHGetDesktopFolder failed\n");
		}
		
		if(str_directory.empty())
		{
			// マイコンピュータ
			SHGetSpecialFolderLocation( hwnd, CSIDL_DRIVES, &directory_item_id );
		}
		else
		{
			directory_item_id = getItemIDList( hwnd, pDesktopFolder, str_directory.c_str() );
		}
		
		ret = pDesktopFolder->BindToObject( directory_item_id, NULL, IID_IShellFolder, (LPVOID *)&pFolder );
		if(ret)
		{
			printf("BindToObject failed\n");
		}
		
	    Py_END_ALLOW_THREADS
	
		int file_num = (int)PySequence_Length(file_list);

		LPITEMIDLIST * item_id_list = new LPITEMIDLIST[file_num];

		for( int i=0 ; i<file_num ; i++ )
		{
			PyObject * pystr_filename = PySequence_GetItem( file_list, i );
	
		    std::wstring str_filename;
		    PythonUtil::PyStringToWideString( pystr_filename, &str_filename );
	
		    Py_BEGIN_ALLOW_THREADS
			item_id_list[i] = getItemIDList( hwnd, pFolder, str_filename.c_str() );
		    Py_END_ALLOW_THREADS

			Py_XDECREF(pystr_filename);
		}
		
	    Py_BEGIN_ALLOW_THREADS

		doContextMenu( hwnd, x, y, pFolder, item_id_list, file_num );

		for( int i=0 ; i<file_num ; i++ )
		{
			pMalloc->Free( item_id_list[i] );
		}
		delete [] item_id_list;

		pFolder->Release();
		
		pMalloc->Free( directory_item_id );
		
		pDesktopFolder->Release();
		
		pMalloc->Release();

	    Py_END_ALLOW_THREADS
	}

	Py_INCREF(Py_None);
	return Py_None;
}

#include "olednd_dataobject.h"
#include "olednd_dropsource.h"

static HDROP CreateHDrop( PyObject * pyfile_list )
{
	FUNC_TRACE;

	HDROP hDrop;

	int file_num = (int)PySequence_Length(pyfile_list);

	std::vector<std::wstring> filename_list;

	size_t total_buffer_size = 0;

	TRACE;

	for( int i=0 ; i<file_num ; i++ )
	{
		TRACE;

		PyObject * pystr_filename = PySequence_GetItem( pyfile_list, i );

		TRACE;

		std::wstring filename;
	    PythonUtil::PyStringToWideString( pystr_filename, &filename );
	    filename_list.push_back(filename);
	    
		TRACE;

	    total_buffer_size += (filename_list[i].length()+1) * sizeof(wchar_t);

		TRACE;

		Py_XDECREF(pystr_filename);

		TRACE;
	}
	
	TRACE;

	hDrop = (HDROP)::GlobalAlloc(GHND,sizeof(DROPFILES) + total_buffer_size + 2);
	if (hDrop == NULL)	return NULL;

	TRACE;

	LPDROPFILES lpDropFile;
	lpDropFile = (LPDROPFILES)::GlobalLock(hDrop);
	lpDropFile->pFiles = sizeof(DROPFILES);		// ファイル名のリストまでのオフセット
	lpDropFile->pt.x = 0;
	lpDropFile->pt.y = 0;
	lpDropFile->fNC = FALSE;
	lpDropFile->fWide = TRUE;					// ワイドキャラの場合は TRUE

	TRACE;

	// 構造体の後ろにファイル名のリストをコピーする。(ファイル名\0ファイル名\0ファイル名\0\0)
	{
		wchar_t * buf = (wchar_t *)(&lpDropFile[1]);
		size_t remaining_buffer_size_in_word = total_buffer_size / sizeof(wchar_t);

		for( int i=0 ; i<file_num ; i++ )
		{
			wcscpy_s( buf, remaining_buffer_size_in_word, filename_list[i].c_str() );
			buf += filename_list[i].length()+1;
			remaining_buffer_size_in_word -= filename_list[i].length() + 1;
		}
		*buf = 0;
	}

	TRACE;

	::GlobalUnlock(hDrop);

	TRACE;

	return	hDrop;
}

static void CreateMedium(CLIPFORMAT cfFormat, HANDLE hObject, FORMATETC *pFormatetc, STGMEDIUM *pmedium)
{
	pFormatetc->cfFormat = cfFormat;
	pFormatetc->dwAspect = DVASPECT_CONTENT;
	pFormatetc->lindex = -1;
	pFormatetc->ptd = NULL;
	pFormatetc->tymed = TYMED_HGLOBAL;

	pmedium->hGlobal = hObject;
	pmedium->tymed = TYMED_HGLOBAL;
	pmedium->pUnkForRelease = NULL;
}

static PyObject * _doDragAndDrop(PyObject* self, PyObject* args)
{
	FUNC_TRACE;

	PyObject * pyfile_list;

    if( ! PyArg_ParseTuple( args, "O", &pyfile_list ) )
        return NULL;
	
	if( !PyTuple_Check(pyfile_list) && !PyList_Check(pyfile_list) )
	{
		PyErr_SetString( PyExc_TypeError, "argument must be a tuple or list." );
		return NULL;
	}

	{
		CDataObject	*dobj = NULL;
		CDropSource	*dsrc = NULL;
		HANDLE		hObject = NULL;
		FORMATETC	fmt;
		STGMEDIUM	medium;
		DWORD		dwEffect;
		int	ret;

		//CDataObjectを作成しCF_HDROP形式のデータを登録
		dobj = new CDataObject();
		if(dobj == NULL) goto error;
		if(!dobj->allocate(1)) goto error;

		if((hObject = CreateHDrop( pyfile_list )) == NULL) goto error;
		CreateMedium(CF_HDROP, hObject, &fmt, &medium);
		if(dobj->SetData(&fmt, &medium, TRUE) != S_OK) goto error;	 //解放はDataObjectに任す

		hObject = NULL;

		dsrc = new CDropSource();
		if(dsrc == NULL) goto error;

		ret = DoDragDrop(dobj, dsrc, DROPEFFECT_COPY,&dwEffect);

		error:

		if(dsrc) dsrc->Release();
		if(dobj) dobj->Release();
		if(hObject) GlobalFree(hObject);
	}

	Py_INCREF(Py_None);
	return Py_None;
}


static PyObject * _getShellLinkInfo( PyObject * self, PyObject * args )
{
	PyObject * pylnk;

	if( ! PyArg_ParseTuple(args,"O", &pylnk ) )
		return NULL;

	std::wstring lnk;
	PythonUtil::PyStringToWideString( pylnk, &lnk );

    HRESULT hres;
    IShellLink *psl;
	WIN32_FIND_DATA wfd;

	TCHAR file[MAX_PATH];
	TCHAR param[MAX_PATH];
	TCHAR directory[MAX_PATH];
	int swmode;

	if( SUCCEEDED(CoInitialize(NULL)) )
	{
        // IShellLink オブジェクトを作成しポインタを取得する
        hres = CoCreateInstance(CLSID_ShellLink, NULL, CLSCTX_INPROC_SERVER,
                                                IID_IShellLink, (void **)&psl);
        if (SUCCEEDED(hres))
        {
            IPersistFile *ppf;

            // IPersistFile インターフェイスの問い合わせをおこなう
            hres = psl->QueryInterface(IID_IPersistFile, (void **)&ppf);
            if (SUCCEEDED(hres))
            {
                // ショートカットをロードする
                hres = ppf->Load( lnk.c_str(), STGM_READ );

                if (SUCCEEDED(hres))
                {
                    // リンク先を取得する
                    psl->GetPath( file, MAX_PATH, &wfd, SLGP_UNCPRIORITY );
    				psl->GetArguments( param, MAX_PATH );
    				psl->GetWorkingDirectory( directory, MAX_PATH );
    				psl->GetShowCmd( &swmode );
                }

                // IPersistFile へのポインタを開放する
                ppf->Release();
            }
            // IShellLinkへのポインタを開放する
            psl->Release();
        }

		CoUninitialize();
	}

    if(SUCCEEDED(hres))
    {
		PyObject * pyret = Py_BuildValue("uuui", file, param, directory, swmode );
    	return pyret;
    }
    else
    {
		PyErr_SetString( PyExc_WindowsError, "can't access to shortcut info." );
		return NULL;
    }
}

static PyObject * _getInternetShortcutInfo( PyObject * self, PyObject * args )
{
	PyObject * pylnk;

	if( ! PyArg_ParseTuple(args,"O", &pylnk ) )
		return NULL;

	std::wstring lnk;
	PythonUtil::PyStringToWideString( pylnk, &lnk );

    HRESULT hres;
    IUniformResourceLocator * psl;

	std::wstring url;

	if( SUCCEEDED(CoInitialize(NULL)) )
	{
        // IUniformResourceLocator オブジェクトを作成しポインタを取得する
        hres = CoCreateInstance(CLSID_InternetShortcut, NULL, CLSCTX_INPROC_SERVER,
                                                IID_IUniformResourceLocator, (void **)&psl);
        if (SUCCEEDED(hres))
        {
            IPersistFile *ppf;

            // IPersistFile インターフェイスの問い合わせをおこなう
            hres = psl->QueryInterface(IID_IPersistFile, (void **)&ppf);
            if (SUCCEEDED(hres))
            {
                // ショートカットをロードする
                hres = ppf->Load( lnk.c_str(), STGM_READ );

                if (SUCCEEDED(hres))
                {
                    // リンク先を取得する
					wchar_t * p;
                    hres = psl->GetURL( &p );
					if (SUCCEEDED(hres))
					{
		            	url = p;

						IMalloc * pMalloc;
						hres = SHGetMalloc(&pMalloc);
						if (SUCCEEDED(hres)){
							pMalloc->Free(p);
							pMalloc->Release();
						}
					}
                }

                // IPersistFile へのポインタを開放する
                ppf->Release();
            }
            // IUniformResourceLocatorへのポインタを開放する
            psl->Release();
        }

		CoUninitialize();
	}

    if(SUCCEEDED(hres))
    {
		PyObject * pyret = Py_BuildValue("u", url.c_str() );
		return pyret;
    }
    else
    {
		PyErr_SetString( PyExc_WindowsError, "can't access to internet shortcut info." );
		return NULL;
    }
}

static PyObject * _chooseColor( PyObject * self, PyObject * args )
{
	HWND hwnd;
	PyObject * py_initial_color = NULL;
	PyObject * py_color_table = NULL;

    if( ! PyArg_ParseTuple( args, "iOO", &hwnd, &py_initial_color, &py_color_table ) )
        return NULL;

	COLORREF initial_color = 0;
	if( PySequence_Check(py_initial_color) )
	{
		int r, g, b;
	    if( ! PyArg_ParseTuple( py_initial_color, "iii", &r, &g, &b ) )
	        return NULL;

	    initial_color = RGB(r,g,b);
	}

	COLORREF color_table[16] = {0};
	if( PySequence_Check(py_color_table) )
	{
		int item_num = (int)PySequence_Length(py_color_table);
		for( int i=0 ; i<item_num && i<16 ; i++ )
		{
			PyObject * item = PySequence_GetItem( py_color_table, i );

			if( PySequence_Check(item) )
			{
				int r, g, b;
			    if( ! PyArg_ParseTuple( item, "iii", &r, &g, &b ) )
			        return NULL;

			    color_table[i] = RGB(r,g,b);
			}
		}
	}

	CHOOSECOLOR cc = {0};

	cc.lStructSize	= sizeof(CHOOSECOLOR);
	cc.hwndOwner	= hwnd;
	cc.rgbResult	= initial_color;
	cc.lpCustColors	= color_table;
	cc.Flags = CC_FULLOPEN | CC_RGBINIT;

	BOOL result = ChooseColor(&cc);

	int color_table_rgb[16][3];
	for( int i=0 ; i<16 ; i++ )
	{
		color_table_rgb[i][0] = GetRValue(cc.lpCustColors[i]);
		color_table_rgb[i][1] = GetGValue(cc.lpCustColors[i]);
		color_table_rgb[i][2] = GetBValue(cc.lpCustColors[i]);
	}

	PyObject * pyret = Py_BuildValue( "i(iii)((iii),(iii),(iii),(iii),(iii),(iii),(iii),(iii),(iii),(iii),(iii),(iii),(iii),(iii),(iii),(iii))",
		result,
		GetRValue(cc.rgbResult), GetGValue(cc.rgbResult), GetBValue(cc.rgbResult),
		color_table_rgb[ 0][0], color_table_rgb[ 0][1], color_table_rgb[ 0][2],
		color_table_rgb[ 1][0], color_table_rgb[ 1][1], color_table_rgb[ 1][2],
		color_table_rgb[ 2][0], color_table_rgb[ 2][1], color_table_rgb[ 2][2],
		color_table_rgb[ 3][0], color_table_rgb[ 3][1], color_table_rgb[ 3][2],
		color_table_rgb[ 4][0], color_table_rgb[ 4][1], color_table_rgb[ 4][2],
		color_table_rgb[ 5][0], color_table_rgb[ 5][1], color_table_rgb[ 5][2],
		color_table_rgb[ 6][0], color_table_rgb[ 6][1], color_table_rgb[ 6][2],
		color_table_rgb[ 7][0], color_table_rgb[ 7][1], color_table_rgb[ 7][2],
		color_table_rgb[ 8][0], color_table_rgb[ 8][1], color_table_rgb[ 8][2],
		color_table_rgb[ 9][0], color_table_rgb[ 9][1], color_table_rgb[ 9][2],
		color_table_rgb[10][0], color_table_rgb[10][1], color_table_rgb[10][2],
		color_table_rgb[11][0], color_table_rgb[11][1], color_table_rgb[11][2],
		color_table_rgb[12][0], color_table_rgb[12][1], color_table_rgb[12][2],
		color_table_rgb[13][0], color_table_rgb[13][1], color_table_rgb[13][2],
		color_table_rgb[14][0], color_table_rgb[14][1], color_table_rgb[14][2],
		color_table_rgb[15][0], color_table_rgb[15][1], color_table_rgb[15][2]
		);
	return pyret;
}

/*
static int _blockDetectorCallback( PyObject * py_report_func, PyFrameObject * frame, int what, PyObject * arg )
{
	static DWORD tick_prev = GetTickCount();
	DWORD tick = GetTickCount();
	DWORD delta = tick-tick_prev;
	tick_prev = tick;
	
	if( delta > 1000 )
	{
		PyObject * pyarglist = Py_BuildValue("()");
		PyObject * pyresult = PyEval_CallObject( py_report_func, pyarglist );
		Py_DECREF(pyarglist);
		if(pyresult)
		{
			Py_DECREF(pyresult);
		}
		else
		{
			PyErr_Print();
		}
	}
	
	return 0;
}

static PyObject * py_report_func;

static PyObject * _enableBlockDetector( PyObject * self, PyObject * args )
{
	PyObject * _py_report_func;

	if( ! PyArg_ParseTuple(args,"O", &_py_report_func ) )
		return NULL;
	
	Py_XDECREF(py_report_func);
	py_report_func = _py_report_func;
	Py_INCREF(py_report_func);

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject * _setBlockDetector( PyObject * self, PyObject * args )
{
	if( ! PyArg_ParseTuple(args,"") )
		return NULL;

	if(py_report_func)
	{
		PyEval_SetProfile( _blockDetectorCallback, py_report_func );
	}

	Py_INCREF(Py_None);
	return Py_None;
}
*/

static PyMethodDef clnch_native_funcs[] =
{
    { "findFile", (PyCFunction)_findFile, METH_VARARGS|METH_KEYWORDS, "" },
    { "enumShare", (PyCFunction)_enumShare, METH_VARARGS|METH_KEYWORDS, "" },
    { "addConnection", (PyCFunction)_addConnection, METH_VARARGS|METH_KEYWORDS, "" },
    { "setFileTime", (PyCFunction)_setFileTime, METH_VARARGS, "" },
    { "popupContextMenu", _popupContextMenu, METH_VARARGS, "" },
    { "doDragAndDrop", _doDragAndDrop, METH_VARARGS, "" },
    { "getShellLinkInfo", _getShellLinkInfo, METH_VARARGS, "" },
    { "getInternetShortcutInfo", _getInternetShortcutInfo, METH_VARARGS, "" },
    { "chooseColor", _chooseColor, METH_VARARGS, "" },
    //{ "enableBlockDetector", _enableBlockDetector, METH_VARARGS, "" },
    //{ "setBlockDetector", _setBlockDetector, METH_VARARGS, "" },
    {NULL, NULL, 0, NULL}
};

// ----------------------------------------------------------------------------

static PyModuleDef clnch_native_module =
{
    PyModuleDef_HEAD_INIT,
    MODULE_NAME,
    "clnch_native module.",
    -1,
    clnch_native_funcs,
	NULL, NULL, NULL, NULL
};

PyMODINIT_FUNC PyInit_clnch_native(void)
{
	CoInitialize(NULL);
	OleInitialize(NULL);
	
    PyObject *m, *d;

    m = PyModule_Create(&clnch_native_module);
    if(m == NULL) return NULL;

    d = PyModule_GetDict(m);

    Error = PyErr_NewException( MODULE_NAME".Error", NULL, NULL);
    PyDict_SetItemString( d, "Error", Error );

    if( PyErr_Occurred() )
    {
        Py_FatalError( "can't initialize module " MODULE_NAME );
    }

	return m;
}
