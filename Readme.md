Steps to Create the Executable
Install PyInstaller:
Open a command prompt and install PyInstaller using pip:

sh
Copy code
pip install pyinstaller
Run PyInstaller:
Use PyInstaller to create the executable. Open a command prompt, navigate to the directory containing your script, and run:

sh
Copy code
pyinstaller --onefile InvoiceOCR.py
Find Your Executable:
After PyInstaller finishes, you'll find your executable in the dist directory within your project folder.

This will package your Python script along with all its dependencies into a single executable file that can be run on any Windows machine without requiring Python to be installed.