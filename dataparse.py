# Things to do:
# 1) Parse recipe discipline data and insert to database

import json
import sys
import psycopg2
from psycopg2 import sql
import os
import sys
import paths

class DatabaseConnection:
	def __init__(self, dbname, autocommit = False):
		try:
			self.connection = psycopg2.connect('dbname={} user=postgres password=password'.format(dbname))
			if autocommit is True:
				self.connection.autocommit = True
			self.cursor = self.connection.cursor()
		except:
			print('Cannot connect to database')
			print(sys.exc_info()[1])
	
	def execute_query(self, query):
		self.cursor.execute(query)
		return self.cursor.fetchall()
	
	def get_tables(self):
		query = '''select table_name 
				from information_schema.tables
				where table_schema = 'public';'''
		self.cursor.execute(query)
		return [res[0] for res in self.cursor.fetchall()]

	def get_columns(self, table_name):
		query = '''select column_name 
				from information_schema.columns 
				where table_name = %s;'''

		self.cursor.execute(query, [table_name])  
		return [res[0] for res in self.cursor.fetchall()]
	
	def insert_to_table(self, table_name, *args): # args are row values
		# Create a string of comma separated placeholders
		values = ', '.join(['%s'] * len(args))							
		
		# Fetch the column names for the provided table concatenate with commas
		columns = ', '.join(self.get_columns(table_name))				
		
		query = "INSERT INTO {{}} ({}) VALUES ({})".format(columns, values)	
		self.cursor.execute(sql.SQL(query).format(sql.Identifier(table_name)), args)

	def select_all(self, table_name):
		query = "SELECT * from {}"
		self.cursor.execute(sql.SQL(query).format(sql.Identifier(table_name)))
		print(self.cursor.fetchall())

	def commit(self):
		self.connection.commit()

class Gw2Database(DatabaseConnection):
	def __init__(self, autocommit = False):
		DatabaseConnection.__init__(self, 'gw2', autocommit)

# Below are generators for parsing the api dump files into valid Python objects for insertion into database

# Generator for items and recipes table
def row_gen(file_path, *args):
	with open(file_path) as file:
		for line in file:
			line = json.loads(line) # NOT json.loads(readline()) otherwise it will skip every other line
			yield [line[arg] for arg in args]

item_gen = row_gen(paths.logs + 'item_dump.txt', 'id', 'name', 'type', 'rarity')
recipe_gen = row_gen(paths.logs + 'recipe_dump.txt', 'id', 'output_item_id', 'output_item_count')

# Generator for ingredients table
def ingredients_gen():
	with open(paths.logs + 'recipe_dump.txt') as f:
		for line in f:
			line = json.loads(line) # This is the entire recipe information
			ingredients = line['ingredients']
			
			for d in ingredients: # Each value is a dictionary of form {item_id: count}
				d['recipe_id'] = line['id'] # Append the recipe_id to the entry
				yield d['recipe_id'], d['item_id'], d['count']

if __name__ == '__main__':
	from utilities.log import Log
	import datetime
	
	def insert(generator, table_name, log_filename):
		gw2db = Gw2Database(autocommit = True)
		counter = 0 
		
		print('Inserting...')
		log = Log(log_filename, paths.logs)
		for row in generator:		
			try:
				gw2db.insert_to_table(table_name, *row) 
			except:
				counter += 1
				log.write(str(row))
				print((sys.exc_info()[1]))
		print('Done')
		
		log.write('{} rows were not inserted'.format(counter))
		log.write('Log created {}'.format(str(datetime.datetime.now())))

	insert(ingredients_gen(), 'ingredients', 'ingredients_not_inserted.txt')


	
	


