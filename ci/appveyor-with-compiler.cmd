:: To build extensions for 64 bit Python 3, we need to configure environment
:: variables to use the MSVC 2010 C++ compilers from GRMSDKX_EN_DVD.iso of:
:: MS Windows SDK for Windows 7 and .NET Framework 4 (SDK v7.1)
::
:: To build extensions for 64 bit Python 2, we need to configure environment
:: variables to use the MSVC 2008 C++ compilers from GRMSDKX_EN_DVD.iso of:
:: MS Windows SDK for Windows 7 and .NET Framework 3.5 (SDK v7.0)
::
:: 32 bit builds do not require specific environment configurations.
::
:: Note: this script needs to be run with the /E:ON and /V:ON flags for the
:: cmd interpreter, at least for (SDK v7.0)
::
:: More details at:
:: https://github.com/cython/cython/wiki/64BitCythonExtensionsOnWindows
:: http://stackoverflow.com/a/13751649/163740
::
:: Author: Olivier Grisel
:: License: CC0 1.0 Universal: http://creativecommons.org/publicdomain/zero/1.0/
SET COMMAND_TO_RUN=%*
SET WIN_SDK_ROOT=C:\Program Files\Microsoft SDKs\Windows
SET WIN_WDK="c:\Program Files (x86)\Windows Kits\10\Include\wdf"
ECHO SDK: %WINDOWS_SDK_VERSION% ARCH: %PYTHON_ARCH%


IF "%PYTHON_VERSION%"=="3.5" (
    IF EXIST %WIN_WDK% (
        REM See: https://connect.microsoft.com/VisualStudio/feedback/details/1610302/
        REN %WIN_WDK% 0wdf
    )
    GOTO main
)

IF "%PYTHON_ARCH%"=="32" (
    GOTO main
)

SET DISTUTILS_USE_SDK=1
SET MSSdk=1
"%WIN_SDK_ROOT%\%WINDOWS_SDK_VERSION%\Setup\WindowsSdkVer.exe" -q -version:%WINDOWS_SDK_VERSION%
CALL "%WIN_SDK_ROOT%\%WINDOWS_SDK_VERSION%\Bin\SetEnv.cmd" /x64 /release

:main

ECHO Executing: %COMMAND_TO_RUN%
CALL %COMMAND_TO_RUN% || EXIT 1
