import sys
import psycopg2
from psycopg2 import sql

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
	
	def test(self):
		return self.connection.status
		
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
	
	def get_all(self):
		''' Returns a list of all table and column names'''
		result = []
		for table_name in self.get_tables():
			result.append((table_name, self.get_columns(table_name)))
		return result
	
	def insert_to_table(self, table_name, **kwargs): 
		'''Keyword Arguments: 
		values(required) - a list of values to be inserted into table_name
		columns(optional) - a list of columns names for when you want
							to insert a record with missing values, will default
							to a full list of column names if not provided'''
		
		# Create a string of comma separated placeholders
		values = ', '.join(['%s'] * len(kwargs['values']))						
		
		if not kwargs['columns']:
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
	
	def close(self):
		self.connection.close()

class Gw2Database(DatabaseConnection):
	def __init__(self, autocommit = False):
		DatabaseConnection.__init__(self, 'gw2', autocommit)

	def name_to_id(self, item_name):
		''' Converts item_name argument to its corresponding item ID listed in 
		database '''
		
		query = "select item_id from items where lower(name) = lower(%s)"
		self.cursor.execute(query, (item_name,))
		try:
			# Note that cursor.fetch methods are iterable, so multiple calls 
			# will exhaust the results.
			return self.cursor.fetchone()[0]
		except:
			return None

	def ingredients(self, item_identifier):
		''' Returns a list of dictionaries for item_identifier argument 
		(name or ID) representing required crafting ingredients one level lower. 
		Return value: [{item_id: <> ,item_name: <> , count: <> }, ...]
		If no lower level ingredients are found, returns None'''
		
		# If item_identifier is an item name, fetch corresponding ID
		if isinstance(item_identifier, str):
			item_id = self.name_to_id(item_identifier)
		else:
			item_id = item_identifier
		
		query = '''SELECT ingredients.item_id, items.name, ingredients.item_count
				FROM recipes INNER JOIN ingredients 
				ON recipes.recipe_id = ingredients.recipe_id
				INNER JOIN items
				ON items.item_id = ingredients.item_id
				WHERE recipes.item_id = %s'''
		# If item_id = None, its value is parsed to NULL
		self.cursor.execute(query, (item_id,))
		
		query_result = self.cursor.fetchall() # [(item_id, item_name, count), ...]
		if query_result:
			return [{'item_id': row[0], 
					 'item_name': row[1], 
					 'count': row[2]} for row in query_result]
		else:
			return None
	
	
	def base_ingredients(self, item_identifier):		
		''' Returns list of dictionaries of item_identifier argument (name or ID) 
		representing the absolute base crafting ingredients.  
		Works by repeatedly calling ingredients().
		Return value: [{item_id: <> ,item_name: <> , count: <> }, ...]'''
		
		if isinstance(item_identifier, str):
			item_id = self.name_to_id(item_identifier)
		else:
			item_id = item_identifier

		result = self.ingredients(item_id) 
		temp = [] # To store intermediate results for each iteration
		
		# If item has no crafting ingredients listed in database
		if result is None: 
			return [{'item_id': item_id, 'count': 1}]
	
		# Should evaluate false only when members in list 'result' all evaluate
		# to None (no lower ingredients)
		while any([self.ingredients(upper['item_id']) for upper in result]):

			for upper in result:	
				# If upper level ingredient is already base, then append to results list
				if self.ingredients(upper['item_id']) is None:
					temp.append(upper)
				
				else: 
					# Get the output quantity of recipe
					query = 'select output_count from recipes where item_id = %s'
					self.cursor.execute(query, (upper['item_id'],))
					output_quantity = self.cursor.fetchone()[0]
					
					# Retrieve lower level ingredients for upper item
					lower_list = self.ingredients(upper['item_id']) # List of dictionaries
					
					#Adjusts the count of lower level ingredients
					for lower in lower_list:
						lower['count'] = int(lower['count']*upper['count']/output_quantity)
					
					# Append the lower level ingredients to results list 
					temp += lower_list
			
			result = temp	# Reset the upper_list to current result list
			temp = [] 		# Important! Otherwise infinite loop
		
		def condense(base_list):
			'''Inner function: merges duplicate dictionaries that have 
			same item_id/item_name value and combining their counts value'''
		
			checked = [] # A tally of item_ids that already exist in result list
			result_list = []
			
			for base_d in base_list:
				item_id = base_d['item_id']
				# If item_id of ingredient dictionary is not in result list, copy dictionary to results
				if item_id not in checked:
					checked.append(item_id)
					result_list.append(base_d)
				# If ingredient dictionary is a duplicate, update the 'count' key for corresponding 
				# entry in result list
				else:
					index = find(result_list, 'item_id', item_id) 
					result_list[index]['count'] += base_d['count']
			return result_list
		
		def find(lst, key, value):
			'''Inner function: Finds the index of first dict from list of dicts 
			where dic[key] == value.  To be used with inner function condense'''
			for i, dic in enumerate(lst):
				if dic[key] == value:
					return i
			return None
		
		return condense(result)

	def vendor_price(self, item_id, *flags): 
		''' Fetches vendor price of item_id arg from the vendor table in database.
		Optional argument flags: 'boolean' causes function to return True or False 
		depending whether item exists in table'''
		
		query = 'SELECT * FROM vendor_items where item_id = %s'
		self.cursor.execute(query, (item_id,))
		try:
			result = self.cursor.fetchone()[1] # (item_id, price, count)
			if boolean:
				return True
			return result
		except:
			if boolean:
				return False
			return 0

if __name__ == '__main__':
	#Oiled Forged Scrap: 82796
	#Green Torch Handle recipe: 4458
	#Rough Sharpening Stone: 9431
	#Lump of Primordium: 19924
	#Gossamer Patch: 76614
	gw2db = Gw2Database()
	for x in gw2db.base_ingredients("berserker's draconic coat"):
		print(x)