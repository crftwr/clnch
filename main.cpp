#include <string>
#include <vector>
#include <list>

#include <windows.h>
#include <shellapi.h>

#if defined(_DEBUG)
#undef _DEBUG
#include "python.h"
#define _DEBUG
#else
#include "python.h"
#endif

//--------------------------------------

int AppMain()
{
	std::wstring exe_dir;

	// Get exe's directory
	{
		wchar_t exe_path_buf[MAX_PATH + 1];
		GetModuleFileName(NULL, exe_path_buf, MAX_PATH);

		exe_dir = exe_path_buf;

		size_t last_backslash_pos = exe_dir.find_last_of(L"\\/");
		if (last_backslash_pos >= 0)
		{
			exe_dir = exe_dir.substr(0, last_backslash_pos);
		}
		else
		{
			exe_dir = L"";
		}
	}

	// Setup environment variable "PATH"
	{
		std::wstring env_path;

		wchar_t tmp_buf[1];
		DWORD ret = GetEnvironmentVariable(L"PATH", tmp_buf, 0);
		if (ret > 0)
		{
			DWORD len = ret;
			wchar_t * buf = (wchar_t*)malloc((len + 1) * sizeof(wchar_t));

			GetEnvironmentVariable(L"PATH", buf, (len + 1) * sizeof(wchar_t));

			env_path = buf;

			free(buf);
		}

		env_path = exe_dir + L"/lib;" + env_path;

		SetEnvironmentVariable(L"PATH", env_path.c_str());
	}

	// Python home
	{
		Py_SetPythonHome(const_cast<wchar_t*>(exe_dir.c_str()));
	}

	// Python module search path
	{
		std::wstring python_path;
		python_path += exe_dir + L";";
		python_path += exe_dir + L"/extension;";
		python_path += exe_dir + L"/lib;";
		python_path += exe_dir + L"/library.zip;";

		Py_SetPath(python_path.c_str());
	}

	// Initialization
	Py_Initialize();

	// Setup sys.argv
	{
		wchar_t * cmdline = GetCommandLine();

		int argc;
		wchar_t ** argv = CommandLineToArgvW(cmdline, &argc);

		PySys_SetArgv(argc, argv);

		LocalFree(argv);
	}

	// Execute python side main script
	{
		PyObject * module = PyImport_ImportModule("clnch_main");
		if (module == NULL)
		{
			PyErr_Print();
		}

		Py_XDECREF(module);
		module = NULL;
	}

	// Termination
	Py_Finalize();

	return 0;
}

#if ! defined(_DEBUG)

int WINAPI WinMain(
	HINSTANCE hInstance,      /* handle to current instance */
	HINSTANCE hPrevInstance,  /* handle to previous instance */
	LPSTR lpCmdLine,          /* pointer to command line */
	int nCmdShow              /* show state of window */
	)
{
	return AppMain();
}

#else

int main(int argc, const char * argv[])
{
	return AppMain();
}

#endif
