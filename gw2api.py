import requests
import json
import sqlite3
import threading
import queue

'''The base URL for all endpoints is https://api.guildwars2.com.  

If the root endpoint (/v2/recipes) is accessed without specifying an id, a list 
of all ids is returned. When multiple ids are requested using the ids parameter, 
a list of response objects is returned.'''

url_v1 = 'https://api.guildwars2.com/'
url_v2 = 'https://api.guildwars2.com/v2/'

def v2_recipes(*recipe_ids):
	'''If the root endpoint (/v2/recipes) is accessed without specifying an id, 
	a list of all ids is returned. When multiple ids are requested using the ids 
	parameter, a list of response objects is returned.'''
	if not recipe_ids:
		response = requests.get(url_v2 + 'recipes')
		return json.loads(response.text)
	
	parameters = {'ids': ','.join([str(x) for x in recipe_ids])}
	response = requests.get(url_v2 + 'recipes', params = parameters)
	return json.loads(response.text)

def v2_items(*item_ids):
	'''
	Endpoints:
	None - Request the list of all available items ids when the root endpoint 
		   (v2/items) has been accessed.
	id - (Optional) Request items for the specified id when accessing the endpoint (v2/items/id). 
		 Cannot be used when specifying the ids parameter.
	
	Parameters:
	lang – (Optional) Request localized information.
	ids - (Optional; Comma Delimited List) Request an array of items for the 
		  specified ids. Cannot be used when using the id endpoint.
	'''
	if not item_ids:
		response = requests.get(url_v2 + 'items')
		return json.loads(response.text)

	parameters = {'ids': ','.join([str(x) for x in item_ids])}
	response = requests.get(url_v2 + 'items', params = parameters)
	return json.loads(response.text)

# This returns a response object, not really for general use
def v2_listings(*item_ids):
	'''
	Parameters:
	ids (optional list of numbers) – A comma-separated list of item ids to query 
	the listings for.
	
	Response:
	If the root endpoint (/v2/commerce/listings) is accessed without specifying 
	an id, a list of all ids is returned. When multiple ids are requested using 
	the ids parameter, a list of response objects is returned.
	
	For each requested item id, an object with the following properties is returned:
	id (number) – The item id.
	buys (array) – A list of all buy listings, ascending from lowest buy order.
	sells (array) – A list of all sell listings, ascending from lowest sell offer.
	
	Each listing object has the following properties:
	listings (number) – The number of individual listings this object refers to 
						(e.g. two players selling at the same price will end up 
						in the same listing)
	unit_price (number) – The sell offer or buy order price in coins.
	quantity (number) – The amount of items being sold/bought in this listing.'''
	parameters = {'ids': ','.join([str(x) for x in item_ids])}
	response = requests.get(url_v2 + 'commerce/listings', params = parameters)
	return response

def v2_listings_buy(item_id):
	response = v2_listings(item_id)
	try:
		price = json.loads(response.text)[0]['buys'][0]['unit_price']
		return price
	except:
		return 0

def v2_listings_sell(item_id):
	response = v2_listings(item_id)
	try:
		price = json.loads(response.text)[0]['sells'][0]['unit_price']
		return price
	except:
		return 0

# Really only use this with v2_items or v2_recipes otherwise it will throw an error
def dump_to_file(api_func, filepath):
	# The api only accepts 200 ids at a time
	all_ids = api_func()
	
	#Break of list of ids into groups of 200 and store in a queue
	start = 0							
	stop = 200
	id_queue = queue.Queue()
	while start < len(all_ids):
		if stop > len(all_ids): 
			stop = len(all_ids)
		id_queue.put(all_ids[start:stop])
		start += 200
		stop += 200					

	def worker(lock):
		while not id_queue.empty():
			ids = id_queue.get()
			results = api_func(*ids)
			
			with open(filepath, 'a+') as dump_file:
				for x in results:
						with lock:
							dump_file.write(json.dumps(x) + '\n')
	
	lock = threading.Lock()
	num_threads = id_queue.qsize()
	threads = []
	
	with open(filepath, 'w+'):
		pass
	
	print("Fetching...")
	for i in range(num_threads):
		thread = threading.Thread(target = worker, args = (lock,))
		thread.start()
		threads.append(thread)
	for thread in threads:
		thread.join()
	print("Done")


if __name__ == '__main__':
	import paths
	
	# Sample ids:
	# Oiled Forged Scrap: 82796
	# Green Torch Handle recipe: 4458
	# Rough Sharpening Stone: 9431
	# Lump of Primordium: 19924
	
	dump_to_file(v2_items, paths.logs + r"\item_dump.txt")