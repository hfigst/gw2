import json
import paths
from database import DatabaseConnection, Gw2Database
import sys

# Below are generators for parsing the api dump files into valid Python objects for insertion into database
# May want to refactor to remove a lot of the boilerplate

# Generator for items and recipes table
def row_gen(file_path, *args):
	with open(file_path) as file:
		for line in file:
			line = json.loads(line) # NOT json.loads(readline()) otherwise it will skip every other line
			yield [line[arg] for arg in args]

item_gen = row_gen(paths.logs + 'item_dump.txt', 'id', 'name', 'type', 'rarity')
recipe_gen = row_gen(paths.logs + 'recipe_dump.txt', 'id', 'output_item_id', 'output_item_count')

# Generator for ingredients table, columns are recipe_id, output_item_id, output_item_count
def ingredients_gen():
	with open(paths.logs + 'recipe_dump.txt') as f:
		for recipe in f:
			recipe = json.loads(recipe)
			ingredients = recipe['ingredients']
			
			# Traverse over sublist
			for ing in ingredients: # Each value is a dictionary of form {item_id: count}
				yield recipe['id'], ing['item_id'], ing['count']

# Generator for recipe_discipline table, columns are recipe_id, discipline
def disciplines_gen():
	with open(paths.logs + 'recipe_dump.txt') as f:
		for line in f:
			line = json.loads(line)
			disciplines = line['disciplines']

			# Traverse over sublist
			for disc in disciplines:
				yield recipe['id'], disc

# Generator for vendor_items table, columns are item_id, price
def vendor_gen():
	with open(paths.logs + 'vendored_items_filtered.json') as f: 
		for line in f:
			line = json.loads(line)

			# Find id -1, which is the copper price
			for ing in line['ingredients']:
				if ing['item_id'] == -1:
					price = ing['count']
					break	
			
			yield line['output_item_id'], price, line['output_item_count']
					
if __name__ == '__main__':
	from utilities.log import Log
	import datetime

	def insert(generator, table_name, log_filename):
		gw2db = Gw2Database(autocommit = True)
		counter = 0 
		
		print('Inserting...')
		log = Log(log_filename, paths.logs)
		log.write(str(gw2db.get_columns(table_name)), end='\n\n')
		for row in generator:		
			print(row)
			try:
				gw2db.insert_to_table(table_name, *row) 
			except:
				counter += 1
				log.write(str(row))
				log.write(str(sys.exc_info()[1]), end = ' ')
				log.write('--------------------------')
		print('Done')
		
		log.write('{} rows were not inserted'.format(counter))
		log.write('Log created {}'.format(str(datetime.datetime.now())))

	insert(vendor_gen(), 'vendor_items', 'vendored_not_inserted.txt')