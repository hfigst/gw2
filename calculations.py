###################################
# Attention!! This code is for the SQLite database.  Needs to be redone for Postgres database
###################################

import sqlite3
import json
import gw2api_v2
import threading
import project_vars

class NotInDatabase(Exception):
	pass

database_path = project_vars.database_path
conn = sqlite3.connect(database_path)
cur = conn.cursor()

def name_to_id(item_name):	
	cur.execute('SELECT id from items WHERE name = ?', (item_name,))
	try:
		return cur.fetchone()[0]
	except:
		raise NotInDatabase('{} was not found in database'.format(item_name))
		

def id_to_name(item_id, ignore = True):			
	cur.execute('SELECT name from items WHERE id = ?', (item_id,))
	try:	
		return cur.fetchone()[0]
	except:
		return NotInDatabase('{} was not found in database'.format(item_id))

def db_ingredient_list(item_id):
	'''Decodes json data from ingredients column and returns a list of 
	dictionaries i.e. [{'item_id': #, 'count': #},...].  Returns None if item 
	has no record in recipes table'''
	cur.execute('SELECT ingredients FROM recipes WHERE output_id = ?', (item_id,))
	try:
		result = cur.fetchone()[0]
		return json.loads(result)
	except:
		return None					#There are two possibilities - item_id doesn't have ingredients or item_id isn't in database in the first place

def is_base(item_id):
	result = db_ingredient_list(item_id)
	if result:
		return False
	else:
		return True

def convert_to_lower(item_dict):
	'''Takes an item dictionary i.e. {'item_id': #, 'count': #} and converts it to 
	LIST of lower level ingredients for that item.'''
	
	if is_base(item_dict['item_id']):	
		return [item_dict]								#if no lower level ingredients

	orig_count = item_dict['count']
	item_id = item_dict['item_id']
	lower_list = db_ingredient_list(item_id)
	for x in lower_list:
		x['count'] = x['count']*orig_count
	return lower_list

def base_ingredients(item_id, shownames = False):		#shownames argument if you just want to return list of ingredients
	result = db_ingredient_list(item_id)

	if not result:  									#Item_id not found in recipes table
		return [{'item_id': item_id, 'count': 1}]

	temp_result = []
	while not all([is_base(item_dict['item_id']) for item_dict in result]):
		for item_dict in result:
			temp_result += convert_to_lower(item_dict)
		result = temp_result
		temp_result = []								#Need to clear temp_results otherwise next loop will keep trying to iterate through to infinitely growing list
	
	if shownames:										#For debugging purposes only
		for d in ingredients:
			d['item_id'] = id_to_name(d['item_id'])	
		
	return result										#result is a LIST of DICTIONARIES

def db_vendor_price(item_id):
	'''If item is sold by master craftsman, fetches price from database'''
	cur.execute('SELECT price from vendor_items WHERE id = ?', (item_id,))
	try:
		return cur.fetchone()[0]
	except:
		return 0

def is_vendored(item_id):
	cur.execute('SELECT "true" from vendor_items WHERE id = ?', (item_id,))
	result = cur.fetchone()
	if result:
		return True
	else:
		return False

def crafting_cost(item_id, shownames = False):		#names argument if you just want to return list of ingredients
	'''Returns the total crafting price of an item assuming you buy each ingredient at the highest bid price.'''
	ingredients = base_ingredients(item_id)
	result_list = []
	
	for item_dict in ingredients:					#Checks whether each ingredient is vendored.  If true, adds it to result list and removes it from ingredients list.  This is done before starting up multiple threads to avoid the comflict with sqlite.
		item_id = item_dict['item_id']
		if is_vendored(item_id):						
			unit_price = db_vendor_price(item_id)
			count = item_dict['count']
			result_list.append({'item_id': item_id, 
								'count': count, 
								'unit_cost': unit_price, 
								'total_cost': unit_price * count
								})
			ingredients.remove(item_dict)
	
	def worker(item_dict):
		item_id = item_dict['item_id']
		count = item_dict['count']					
			
		unit_cost = gw2api_v2.v2_listings_buy(item_id)			
		if unit_cost == 0:
			unit_cost = gw2api_v2.v2_listings_sell(item_id)	#Some items have base ingredients with no buy or sell listing so value defaults to 0

		total_cost = unit_cost * count
		result_list.append({'item_id': item_id, 
							'count': count, 
							'unit_cost': unit_cost, 
							'total_cost': total_cost})
	
	threads_list = []
	for item_dict in ingredients:
		t = threading.Thread(target = worker, args = (item_dict, ))
		t.start()
		threads_list.append(t)
	for t in threads_list:
		t.join()

	
	if shownames:								   			# Returns complete ingredient information											
		unknown_ids = []
		for d in result_list:								
			try:
				d['item_id'] = id_to_name(d['item_id'])
			except:
				unknown_ids.append(d['item_id'])
		if unknown_ids:
			print('The following ids were not found in the database:')
			print('\n'.join(unknown_ids))

		return result_list

	return sum([result['total_cost'] for result in result_list])

def cmd_main(): 			
	import argparse
	parser = argparse.ArgumentParser()
	
	group = parser.add_mutually_exclusive_group()
	group.add_argument('-c', '--craft', help = 'crafting price of multiple items', type = str) # nargs='+' -> multiple args but at least one
	group.add_argument('-s', '--sell', help = 'selling price of multiple itmes', type = str)

	args = parser.parse_args()		#namespace object containing arguments

	try:
		if args.craft:
			print(crafting_cost(name_to_id(args.craft)), end='')
		elif args.sell:
			print(gw2api_v2.v2_listings_sell(name_to_id(args.sell)), end='')
	except:
		print(0)
	

#Remember to enclose arguments containing spaces with DOUBLE quotes

if __name__ == '__main__':
	
	#Oiled Forged Scrap: 82796
	#Green Torch Handle recipe: 4458
	#Rough Sharpening Stone: 9431
	#Lump of Primordium: 19924
	print(crafting_cost(name_to_id("Pharus"), shownames = True))