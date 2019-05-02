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
	
	def execute_query(self, query): # This needs to be fixed!!
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

	# Converts item's id -> name or name -> id
	def lookup(self, item):
		if isinstance(item, int):
			query = 'select name from items where item_id = %s'
			self.cursor.execute(query, (item,))
		elif isinstance(item, str):
			query = "select item_id from items where lower(name) = lower(%s)"
			# lower(name) doesn't work consistently for some reason
			# But this works and I don't know why:
			# self.execute_query("select item_id from items where lower(name) = 'oiled forged scrap'"))
			self.cursor.execute(query, (item,))
			# print(self.cursor.query)
		# Note that cursor.fetch methods are iterable, so multiple calls will exhaust the results
		try:
			return self.cursor.fetchone()[0]
		except:
			return None

	# Returns a list of ingredients exactly one level lower for the item argument. Return value is a list of DICTIONARIES
	def ingredients(self, item):
		# Converts name -> id if needed
		if isinstance(item, str):
			item = self.lookup(item)
		
		query = '''SELECT ingredients.ingredient_item_id, items.name, ingredients.item_count
				FROM recipes INNER JOIN ingredients 
				ON recipes.recipe_id = ingredients.recipe_id
				INNER JOIN items
				ON items.item_id = ingredients.ingredient_item_id
				WHERE recipes.output_item_id = %s'''
		# If item_id = None, its value is converted to NULL
		self.cursor.execute(query, (item,))
		
		query_result = self.cursor.fetchall() # This is a list of tuples
		if query_result:
			return [{'item_id': row[0], 
					 'item_name': row[1], 
					 'count': row[2]} for row in query_result]
		# If no results found return None therefore function can also act as a logical check whether the item provided
		# has base ingredients 
		else:
			return None
	
	# Returns list of lowest level ingredients of item argument. Item argument can be string or integer
	def base(self, item):		
		result = self.ingredients(item) 
		temp = [] # To store intermediate results for each iteration
		
		# In the case there is no ingredients
		if result == None: 
			return [{'item_id': item, 'count': 1}]

		# Should evaluate false only when ingredients it list 'result' all evaluate to None (no lower ingredients)
		while any([self.ingredients(upper['item_id']) for upper in result]):

			for upper in result:	
				# If upper level ingredient is already base, then append to results list
				if self.ingredients(upper['item_id']) is None:
					temp.append(upper)
				
				else: 
					# Get the output quantity of recipe
					query = 'select output_item_count from recipes where output_item_id = %s'
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
		
		######Inner function block######
		def condense(base_list):
			checked = [] # A tally of item_ids that already exist in result list
			result_list = []
			for base_d in base_list:
				item_id = base_d['item_id']

				# If item_id of ingredient dictionary is not in result list, copy dictionary to results
				if item_id not in checked:
					checked.append(item_id)
					result_list.append(base_d)
				# If ingredient dictionary is a duplicate, update the 'count' key for corresponding entry in result list
				else:
					index = find(result_list, 'item_id', item_id) 
					result_list[index]['count'] += base_d['count']
			return result_list
		def find(lst, key, value):
			# Finds the index of first dict from list of dicts where dic[key] == value
			for i, dic in enumerate(lst):
				if dic[key] == value:
					return i
			return None
		######Inner function block end######
		
		return condense(result)

	# Returns vendor price or 0 if not found
	def vendor_price(self, item_id):
		query = 'SELECT * FROM vendor_items where item_id = %s'
		self.cursor.execute(query, (item_id,))
		try:
			return self.cursor.fetchone()[1] # (item_id, price, count)
		except:
			return 0

if __name__ == '__main__':
	#Oiled Forged Scrap: 82796
	#Green Torch Handle recipe: 4458
	#Rough Sharpening Stone: 9431
	#Lump of Primordium: 19924
	#Gossamer Patch: 76614
	gw2db = Gw2Database()
	for x in gw2db.base('warbeast greaves'):
		print(x)
	