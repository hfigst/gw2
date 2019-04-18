import requests
import json

'''Official documentation on gwspidy's api can be found at:
https://github.com/rubensayshi/gw2spidy/wiki/API-v0.9.'''

def getTypes():
	return genericRequest('types')

def getDisciplines():
	'''Scribe is missing somehow'''
	return genericRequest('disciplines')
	
def getRarities():
	return genericRequest('rarities')

def getItemsofType(type_id='all'): 
	'''Use getItems instead for the most complete list of item ids''
	   Path - /api/{version}/{format}/all-items/{type}'''
	return genericRequest('all-items', type_id)

def getItems(type_id='all', *, page = '', **parameters):
	'''Parameters - sort_trending and/or filter_ids
	   Path - /api/{version}/{format}/items/{type}/{page}'''
	return paginatedRequest('items', type_id, page=page, **parameters)
 
def getItemData(item_id):
	'''Returns full data of ONE item
	   Path - /api/{version}/{format}/item/{dataID}'''
	return normalRequest('item' ,item_id)

def getItemListings(item_id, buy_or_sell, *, page = ''):
	'''Path - /api/{version}/{format}/listings/{dataId}/{sell-or-buy}/{page}'''
	return paginatedRequest('listings', item_id, buy_or_sell, page = page)
	
def searchItemByName(name, *, page):
	'''Path - /api/{version}/{format}/item-search/{name}/{page}'''
	return paginatedRequest('item-search', name, page)

def getRecipes(type_id = 'all', *, page = ''):
	'''Path - /api/{version}/{format}/recipes/{type}/{page}'''
	return paginatedRequest('recipes', type_id, page=page,)

def getRecipeData(recipe_id):
	'''Can only return ONE recipe's data
	   Path - /api/{version}/{format}/recipe/{recipe_id}'''
	return genericRequest('recipe', recipe_id)

def genericRequest(*args, **parameters):
	path = '/'.join([str(arg) for arg in args])
	url = 'http://www.gw2spidy.com/api/v0.9/json/{}'.format(path)
	response = requests.get(url, params = parameters)
	return response

def paginatedRequest(*args, page = '', **parameters):
	'''For endpoints that can return specific pages'''
	path = '/'.join([str(arg) for arg in args])
	url = 'http://www.gw2spidy.com/api/v0.9/json/{}/{}'.format(path, str(page))
	response = requests.get(url, params = parameters)
	return response
	
if __name__ == '__main__':	
	# Sample ids:
	# Oiled Forged Scrap: 82796
	# Green Torch Handle recipe: 4458
	# Rough Sharpening Stone: 9431
	
	
	'''Getting all pages of recipe info'''
	result = json.loads(getRecipes().text)	
	total_pages = result['last_page']		# Getting the last page number
	
	output_file = 'all_recipes.txt'
	with open(output_file, 'w+') as f:	
		
		page = 1
		while page <= total_pages:
			result = json.loads(getRecipes(page = page).text)
			for x in result['results']:
				'''Making each result database friendly'''
				x = (x['data_id'], x['name'], x['result_count'], x['result_item_data_id'])
				x = [str(item) for item in x]
				x[1] = repr(x[1])			# Some items have quotes in them
				f.write(','.join(x) + '\n')	
			
			print('page {} finished'.format(page))
			page += 1

