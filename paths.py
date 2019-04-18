import os
import sys

# Joins the full path of the project root directory to any subdirectories.  This will only work properly 
# if this module (paths.py) is in the project root directory
def fullpath(folder_name):
	root_dir = os.path.dirname(__file__)
	path = os.path.normpath(os.path.join(root_dir, folder_name)) # Blank string for the trailing separator
	return path + os.path.sep

# Folder location of SQLite database (will probably be deprecated)
database = fullpath('database')

# Folder location of any text dumps or log files.
logs = fullpath('logs')

if __name__ == '__main__':
	print(logs)
	print(database)
