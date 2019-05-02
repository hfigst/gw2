''' Contains the Log class, a slightly more convenvient way of writing textlog files without having to
deal with file paths and context managers'''

import os
import sys

class Log:
	# If no path is provided this class will create the log file in the same directory as the top level script
	def __init__(self, filename, folder_path=0):
		self.filename = filename
		
		#If a specific folder path is provided
		if folder_path:
			self.path = os.path.normpath(os.path.join(folder_path, filename))
		else:	
			# Get the directory of the top level script and join it with the provided filename
			current_dir = os.path.dirname(sys.modules['__main__'].__file__)
			self.path = os.path.normpath(os.path.join(current_dir, filename))

		# Create a blank log file
		with open(self.path, 'w+') as f:
			pass
	
	def write(self, string, end='\n'):
		with open(self.path, 'a+') as f:
			f.write(string + end)

if __name__ == '__main__':
	import datetime
	
	testlog = Log('testlog.txt')
	testlog.write('hello', 6)
	testlog.write('world', 6)
	testlog.write(str(datetime.datetime.now()))

		


	

