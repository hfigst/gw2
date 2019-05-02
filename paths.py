import os
import sys


def fullpath(folder_name):
	'''Joins the full path of the project root directory to any subdirectories.  This will only work properly 
	if this module (paths.py) is in the project root directory'''
	
	root_dir = os.path.dirname(__file__) # Directory of paths.py
	path = os.path.normpath(os.path.join(root_dir, folder_name))
	return path + os.path.sep

# Folder lpath of SQLite database (will probably be deprecated)
database = fullpath('database')

# Folder path of any text dumps or log files.
logs = fullpath('logs')

if __name__ == '__main__':
	print(logs)
	print(database)
	print(__file__)
