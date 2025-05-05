import tkinter as tk
from tkinter import ttk, messagebox
import os
import shutil
import requests
import zipfile
import io
import subprocess

# --- Configuration (Windows Specific) ---
# URL for platform tools download for Windows
DOWNLOAD_URL_WINDOWS = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"

# The final target directory where the contents of the 'platform-tools' folder
# from the zip will be extracted.
TARGET_INSTALL_DIR_WINDOWS = "C:\\Platform-tools"

# --- Helper Functions ---

def is_adb_in_path():
    """Checks if adb.exe executable is found in the system's PATH on Windows."""
    # shutil.which handles '.exe' extension automatically on Windows
    return shutil.which("adb") is not None

def download_and_extract_adb(url, target_dir, status_callback):
    """Downloads the zip file and extracts platform-tools contents directly into the target directory."""
    status_callback("Starting download...")
    try:
        # Use stream=True to handle large files efficiently
        response = requests.get(url, stream=True)
        response.raise_for_status() # Raise an exception for bad status codes (e.g., 404)

        total_size = int(response.headers.get('content-length', 0))
        bytes_downloaded = 0

        status_callback("Downloading...")
        # Download in chunks and write to a buffer
        zip_buffer = io.BytesIO()
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                zip_buffer.write(chunk)
                bytes_downloaded += len(chunk)
                # Update status with progress (optional, might still cause slight GUI freeze without threading)
                progress = (bytes_downloaded / total_size) * 100 if total_size else 0
                status_callback(f"Downloading... {progress:.1f}% ({bytes_downloaded}/{total_size} bytes)", update_gui=True)


        zip_buffer.seek(0) # Go back to the start of the buffer

        status_callback("Download complete. Extracting...")

        # Ensure the target directory exists
        os.makedirs(target_dir, exist_ok=True)

        status_callback(f"Extracting to {target_dir}...")

        # Extract the zip file
        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            # The zip usually contains a single 'platform-tools' folder at the root
            # Find the root directory inside the zip (expecting 'platform-tools')
            zip_root_dir = None
            for name in zip_ref.namelist():
                 if '/' in name:
                      potential_root = name.split('/')[0]
                      if potential_root == 'platform-tools':
                           zip_root_dir = potential_root
                           break
                 elif name.endswith('/') and name.strip('/') == 'platform-tools': # Handle root dir entry itself
                      zip_root_dir = name.strip('/')
                      break

            if not zip_root_dir:
                 # Fallback: if 'platform-tools' wasn't found explicitly, check if there's only one top-level dir
                 top_level_dirs = set()
                 for name in zip_ref.namelist():
                      if '/' in name:
                           top_level_dirs.add(name.split('/')[0])
                 if len(top_level_dirs) == 1:
                      zip_root_dir = list(top_level_dirs)[0]
                 else:
                      raise Exception("Could not find expected 'platform-tools' directory in the zip.")


            # Extract contents of the platform-tools directory directly into the target_dir
            for member in zip_ref.namelist():
                 if member.startswith(zip_root_dir + '/') and not member.endswith('/'): # Only extract files within the root dir
                      # Construct the target path by joining target_dir with the path relative to the zip_root_dir
                      # e.g., if member is 'platform-tools/adb.exe', target_path will be 'C:\Platform-tools\adb.exe'
                      relative_path = member[len(zip_root_dir)+1:] # Get path relative to platform-tools/
                      target_path = os.path.join(target_dir, relative_path)
                      os.makedirs(os.path.dirname(target_path), exist_ok=True) # Ensure subdirectories exist within target_dir
                      try:
                           with zip_ref.open(member) as source, open(target_path, "wb") as target:
                                shutil.copyfileobj(source, target)
                      except Exception as e:
                           print(f"Error extracting {member} to {target_path}: {e}") # Log extraction errors
                           # Continue extraction but report error
                           status_callback(f"Extraction error on {member}: {e}", update_gui=True)


            # Verify extraction by checking for adb.exe executable in the target path
            adb_exe_path = os.path.join(target_dir, "adb.exe")
            if not os.path.exists(adb_exe_path):
                 # Check if any executable is there as a last resort for troubleshooting
                 if os.path.exists(target_dir):
                     executables_found = [f for f in os.listdir(target_dir) if f.endswith('.exe')]
                     if executables_found:
                         raise Exception(f"Extraction failed: adb.exe not found in {target_dir}. Found executables: {', '.join(executables_found)}")
                     else:
                          raise Exception(f"Extraction failed: {target_dir} exists but appears empty or missing executables.")
                 else:
                      # This case should ideally not happen if os.makedirs was successful
                      raise Exception(f"Extraction failed: Target directory {target_dir} was not created or is inaccessible.")


        status_callback(f"Extraction complete! ADB tools are in: {target_dir}", update_gui=True)
        return target_dir # Return the final path where contents were extracted

    except requests.exceptions.RequestException as e:
        status_callback(f"Download failed: {e}", update_gui=True)
        messagebox.showerror("Download Error", f"Failed to download ADB tools from {url}:\n{e}")
        return None
    except zipfile.BadZipFile:
         status_callback("Extraction failed: Downloaded file is not a valid zip.", update_gui=True)
         messagebox.showerror("Extraction Error", "Downloaded file is corrupted or not a zip.")
         return None
    except Exception as e:
        status_callback(f"An error occurred: {e}", update_gui=True)
        messagebox.showerror("Error", f"An unexpected error occurred during download or extraction:\n{e}")
        return None

def add_to_user_path(directory_to_add, status_callback):
    """Attempts to add the specified directory to the current user's PATH using setx."""
    status_callback(f"Attempting to add {directory_to_add} to User PATH...", update_gui=True)

    # Use setx command to append to the user's PATH
    # %PATH% inside the quotes refers to the *current* PATH environment variable
    # This adds the directory to the END of the user's PATH
    command = f'setx PATH "%PATH%;{directory_to_add}"'

    try:
        # Use shell=True because setx is a built-in command or relies on the shell's environment
        # capture_output=True captures stdout/stderr, text=True decodes it
        # check=False because setx returns 0 even if it prints warnings
        result = subprocess.run(command, shell=True, check=False, capture_output=True, text=True)

        # setx returns 0 on success even if it prints a "SUCCESS: Specified value was saved" message
        # Check returncode for primary success indicator
        if result.returncode == 0:
            status_callback("Successfully attempted to add to User PATH.", foreground="green", update_gui=True)
            # Print setx output for debugging if needed
            print(f"setx stdout:\n{result.stdout}")
            if result.stderr: print(f"setx stderr:\n{result.stderr}")
            return True
        else:
            error_msg = result.stderr or result.stdout # setx errors usually go to stderr or stdout
            status_callback(f"Failed to add to User PATH: {error_msg.strip()}", foreground="red", update_gui=True)
            print(f"setx stdout:\n{result.stdout}")
            print(f"setx stderr:\n{result.stderr}")
            messagebox.showerror(
                "PATH Update Failed",
                f"Failed to automatically add {directory_to_add} to your User PATH.\n\nDetails:\n{error_msg.strip()}\n\nYou may need to add it manually.\n\nConsult online resources for 'how to add to Windows user path'."
            )
            return False

    except FileNotFoundError:
        status_callback("Error: setx command not found.", foreground="red", update_gui=True)
        messagebox.showerror("Error", "The 'setx' command was not found on your system.")
        return False
    except Exception as e:
        status_callback(f"An unexpected error occurred while updating PATH: {e}", foreground="red", update_gui=True)
        messagebox.showerror("Error", f"An unexpected error occurred while attempting to update your PATH:\n{e}")
        return False


# --- GUI Class ---

class AdbCheckerApp:
    def __init__(self, root):
        self.root = root
        root.title("ADB Path Checker and Installer (Windows)")
        root.geometry("450x350")

        self.install_dir = TARGET_INSTALL_DIR_WINDOWS
        self.download_url = DOWNLOAD_URL_WINDOWS

        # --- GUI Elements ---
        self.status_label = ttk.Label(root, text="Checking ADB status...")
        self.status_label.pack(pady=(20, 5)) # Add padding at top

        self.check_button = ttk.Button(root, text="Check ADB Status", command=self.check_adb_status)
        self.check_button.pack(pady=10)

        self.download_button = ttk.Button(root, text="Download & Install ADB", command=self.on_download_click)
        self.download_button.pack(pady=10)

        self.instructions_label = ttk.Label(root, text="", wraplength=400, justify="left")
        self.instructions_label.pack(pady=10, padx=10)


        # --- Initial Check ---
        self.check_adb_status()


    def update_status(self, message, foreground=None, update_gui=False):
        """Updates the status label text and optional color."""
        self.status_label.config(text=message)
        if foreground:
             self.status_label.config(foreground=foreground)
        else:
             # Reset color to default if not specified
             self.status_label.config(foreground="black")

        if update_gui:
            self.root.update_idletasks() # Force GUI refresh


    def check_adb_status(self):
        """Checks if ADB is in PATH and updates the GUI for Windows."""
        self.update_status("Checking ADB status in PATH...")
        self.instructions_label.config(text="") # Clear previous messages


        if is_adb_in_path():
            self.update_status("✅ ADB is found in your PATH!", foreground="green")
            self.download_button.config(state=tk.DISABLED)
            self.instructions_label.config(text="ADB is correctly configured. You can use 'adb' from any Command Prompt or PowerShell window.", foreground="black")

        else:
            # ADB not found
            self.update_status("❌ ADB not found in your PATH.", foreground="red")
            self.download_button.config(state=tk.NORMAL)
            self.instructions_label.config(
                 text=f"Click 'Download & Install ADB' to get the latest tools.\nThey will be saved directly to:\n{self.install_dir}\n\nThe script will then attempt to automatically add this location to your User PATH.",
                 foreground="blue"
            )


    def on_download_click(self):
         """Handles the download button click event."""
         # Disable buttons during the process
         self.download_button.config(state=tk.DISABLED)
         self.check_button.config(state=tk.DISABLED)
         self.instructions_label.config(text="") # Clear previous instructions

         # Removed mention of administrator privileges
         confirmed = messagebox.askyesno(
              "Confirm Download & Install",
              f"ADB tools will be downloaded and extracted directly to:\n{self.install_dir}\n\nAfter extraction, the script will automatically attempt to add this path to your User Environment Variables.\n\nDo you want to continue?"
         )

         if confirmed:
              # Perform download and extraction (blocking call in main thread)
              self.update_status(f"Initiating download and extraction to {self.install_dir}...", update_gui=True)
              actual_adb_dir = download_and_extract_adb(
                  self.download_url,
                  self.install_dir, # Pass the target installation directory
                  self.update_status # Pass the status update method
              )

              if actual_adb_dir:
                  # Attempt to add to PATH
                  path_attempt_successful = add_to_user_path(actual_adb_dir, self.update_status)

                  # Provide instructions to restart and rerun
                  final_message = (
                      f"ADB tools extracted to {actual_adb_dir}.\n"
                      f"Attempted to add this location to your User PATH.\n\n"
                      f"For the changes to take effect, you may need to RESTART your computer.\n"
                      f"After restarting, please RUN THIS SCRIPT AGAIN to verify if ADB is now found in your PATH."
                  )

                  # Update status label to indicate next steps
                  self.update_status("Installation complete. Please restart and rerun.", foreground="blue")
                  self.instructions_label.config(text=final_message, foreground="black") # Set message

                  # Also show in a message box
                  messagebox.showinfo("Installation Complete - Action Required", final_message)

                  # Keep download button disabled after successful extraction and path attempt
                  self.download_button.config(state=tk.DISABLED)
                  self.check_button.config(state=tk.NORMAL) # Re-enable check button


              else:
                   # Download/Extraction failed
                   self.update_status("Download and extraction failed.", foreground="red")
                   # Re-enable button if it failed
                   self.download_button.config(state=tk.NORMAL)
                   self.check_button.config(state=tk.NORMAL) # Re-enable check button


# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = AdbCheckerApp(root)
    root.mainloop()