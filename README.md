# ADB Path Checker and Installer (for Windows)

## Project Description

This is a simple graphical user interface (GUI) application for Windows designed to help users quickly check if the Android Debug Bridge (ADB) tool is installed and correctly set up in their system's PATH environment variable. If ADB is not found, the application provides an easy way to automatically download the latest Android Platform-Tools, extract them to a standard location (`C:\Platform-tools`), and attempt to configure your system's PATH so you can use `adb` commands from any terminal window.

This application is provided as a standalone executable (`.exe`) that does **not** require Python to be installed on your computer to run.

## Features

* Quickly checks for the presence of `adb.exe` in your system's PATH.
* Provides clear visual feedback (found or not found).
* Offers automatic download of the latest Android Platform-Tools if ADB is missing.
* Extracts tools to `C:\Platform-tools`.
* Attempts to automatically add `C:\Platform-tools` to your User PATH environment variable.
* Provides instructions on how to manually verify the installation and PATH update.
* Packaged as a single, standalone executable for Windows (does not require Python installation).

## How to Get the Application Executable

The easiest way to get the application executable (`.exe`) is to download it directly from the **GitHub Releases** page for the specific version:

1.  Go directly to the **[ADB Path Checker Installer v1.0.0 Release Page](https://github.com/Djkawada/ADB-Path-Checker-Installer/releases/tag/v1.0.0)**.
2.  Under the "Assets" section on that release page, find the **`ADB_Path_Checker_Installer.exe`** file.
3.  Click on the `.exe` file name to download it.

*(Downloading the source code zip/tar.gz from this page or the main repository page is typically for developers who want to view or build the code themselves, not for end-users who just want to run the application.)*

## How to Run the Executable

1.  Locate the downloaded `ADB_Path_Checker_Installer.exe` file on your computer.
2.  **Double-click** the `.exe` file to launch the application.
3.  The application will perform an initial check for ADB in your PATH automatically.
4.  Observe the status message on the application window.
5.  If ADB is not found, the "Download & Install ADB" button will be enabled. Click it to proceed with the automatic installation.
6.  Follow any prompts that appear.
7.  After the installation process attempts to add ADB to your PATH, the application will instruct you that you **may need to RESTART your computer** for the PATH changes to fully take effect in all applications and terminal windows.
8.  After restarting, **run the `ADB_Path_Checker_Installer.exe` again** to perform another check and verify that ADB is now found in your PATH.

## How it Works (Briefly)

The application is written in Python using the `tkinter` library for the GUI. It utilizes standard system tools and Python libraries to:
* Check the PATH (`shutil`).
* Download the ADB Platform-Tools zip file from Google's servers (`requests`).
* Extract the necessary files from the zip (`zipfile`).
* Create the installation directory (`os`).
* Attempt to modify the User PATH environment variable using the `setx` command (`subprocess`).

The entire Python environment and script are packaged into a single executable using PyInstaller, so the end-user doesn't need any prior Python setup.

## Building from Source (For Developers)

If you are a developer and wish to build the executable from the Python script yourself:

1.  Make sure you have Python 3.6 or newer installed.
2.  Install the required Python libraries, including PyInstaller:
    ```bash
    pip install requests pyinstaller
    ```
3.  Clone this repository or download the source code zip.
4.  Open your terminal (Command Prompt or PowerShell) and navigate to the root directory of the project (where `ADB_Path_Checker_Installer.py` is located).
5.  Run the PyInstaller command:
    ```bash
    pyinstaller --windowed --onefile --name "ADB_Path_Checker_Installer" ADB_Path_Checker_Installer.py
    ```
6.  The standalone executable `ADB_Path_Checker_Installer.exe` will be created in the `./dist` folder.

## License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.
