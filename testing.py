# Use this file to test whether other modules run properly and prototype code

import gw2api
import dataparse
import paths
import sys
import json

def ingredients_gen():
	with open(paths.logs + 'recipe_dump.txt') as f:
		for line in f:
			line = json.loads(line) # This is the entire recipe information
			ingredients = line['ingredients']
			
			for d in ingredients: # Each value is a dictionary of form {item_id: count}
				d['recipe_id'] = line['id'] # Append the recipe_id to the entry
				yield d['recipe_id'], d['item_id'], d['count']

x = gen()

for i in range(10):
	print(next(x))







