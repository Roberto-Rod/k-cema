# README #

This project was developed using [Python 3.11.2 for Windows 64-bit](https://www.python.org/downloads/release/python-3112/). 

It has been tested using Windows 10, 64-bit.

## Building the Executable ##

### Pre-requisites ###

1.  The executable will fail to run unless the usage of the deprecated 'imp' module by ansiwrap is patched out.
    To do this, edit the file "C:\Users\<user>\AppData\Local\Programs\Python\Python311\Lib\site-packages\ansiwrap\core.py" as follows:

    Change line "import imp" to:
        import importlib.util

    Change line "a_textwrap = imp.load_module('a_textwrap', *imp.find_module('textwrap3'))" to (3 lines):
        module_spec = importlib.util.find_spec('textwrap')
        a_textwrap = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(a_textwrap)

2.  If they exist already, delete the "build" and "dist" folders from the root folder (where ntm_mb_ehb_rf_board_test.py resides).
    This is required for a clean build since the --clean option for pyinstaller fails due to permission errors.

### Instructions ###

The excutable and associated files/folders are built using the 'pysinstaller' package, using this webpage as a guide:
https://www.pythonguis.com/tutorials/packaging-tkinter-applications-windows-pyinstaller/

1.  Create a Windows batch file with the following command lines inside it:

TBD

2.  Save the batch file in the root folder (e.g. build_executable.bat), then run it.

    This will create two new folders:
    - build (contains the temporary files used during the build process)
    - dist (contains the executable itself plus file/folder dependencies)

3.  The first time the executable is run there will be a significant delay before the UI window appears.
    The delay is negligible after this.

### De-bugging Executable Problems ###

If the excutable is built with the pyinstaller option line '--noconsole ^' omitted and the line '--debug="imports" ^' added,
then running the executable file will spawn an additional console window that contains useful debug information on launch of the EXE
as well as the standard output stream during runtime.

## Creating the Installer ##

The Windows installer is built using InstallForge, in accordance with the instructions given here https://www.pythonguis.com/tutorials/packaging-tkinter-applications-windows-pyinstaller.

Open the InstallForge project file TBD for recommended settings.

