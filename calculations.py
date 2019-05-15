from database import Gw2Database
import gw2api
from threading import Thread
from queue import Queue
import os

# Returns a dictionary of form {item_id: unit_cost, ... }
def make_vendor_dict():
    gw2db  = Gw2Database()
    query = 'select item_id, price from vendor_items'
    gw2db.cursor.execute(query)
    return dict(gw2db.cursor.fetchall())

def vendor_price(item_id, vendor_dict):
    if item_id in vendor_dict.keys():
        return vendor_dict[item_id]
    else:
        return None

class ThreadPool:
    def __init__(self, num_threads):
        
        # Reference to these objects will be passed to each thread
        self.queue = Queue()
        self.results = []
    
        self.num_threads = num_threads
    
    def add_task(self, func, *args, **kwargs):
        '''Adds a tuple to the queue containing the function and arguments to be called by each thread'''
        self.queue.put((func, args, kwargs)) # (func, [], {}), Note inner parenthesis
    
    def start(self):
        '''Start all threads'''
        for i in range(self.num_threads):
            # Create thread objects and pass in ThreadPool's queue and results object for thread objects to work on
            WorkerThread(self.queue, self.results)
    
    def join(self):
        '''Blocks execution until queue has been exhausted'''
        self.queue.join()
    
    def stop_threads(self):
        '''Populate queue with None tuples to signal threads to stop'''
        for i in range(self.num_threads):
            self.queue.put((None, None, None))

class WorkerThread(Thread):
    def __init__(self, queue, results,):
        #queue, results, lock arguments are references to the ThreadPool object.
        Thread.__init__(self)
        self.queue = queue
        self.results = results
        self.start() 
    
    def run(self):
        while True:
            func, args, kwargs = self.queue.get()
            # Stop the thread when it fetches None from queue
            if func is None:
                # print('Thread {} terminating'.format(self.name))
                break
            
            self.results.append(func(*args, **kwargs))   
            self.queue.task_done()

def crafting_cost(item_identifier, info = False):
    ''' Note that this function is threaded and establishes a database connection.
    Arguments: 'item_identifier' is either an item name or id
               
               info is a flag which when set forces function to return a list 
               of dictionaries with full information about ingredient costs
               Return value: [{item_id: , item_name, count:, unit_cost: ,total_cost: }, ...]
               '''
    
    gw2db = Gw2Database()
    vendor_dict = make_vendor_dict() # To be accessed by worker function
    ingredients = gw2db.base_ingredients(item_identifier)
    
    # Defining worker function
    def worker(ingredient):
        '''Ingredient argument is a dictionary from base ingredients list.  
        Looks up the item_id against gw2 api's TP listings.
        Returns an augmented dictionary with two additional keys - 'unit_cost' and 'total_cost' '''
        
        item_id = ingredient['item_id']
        
        # We assume that the priority of where you buy the item from will be 
        # 1) vendor, 2) buy listings, 3) sell listings
        unit_cost = vendor_price(item_id, vendor_dict)
        if unit_cost is None:
            unit_cost = gw2api.v2_listings_buy(item_id)
            if unit_cost == 0:
                unit_cost = gw2api.v2_listings_sell(item_id)

        ingredient['unit_cost'] = unit_cost
        ingredient['total_cost'] = unit_cost * ingredient['count']

        return ingredient

    pool = ThreadPool(len(ingredients))
    # Populate the threadpool queue with dictionaries from ingredients list
    for ingredient in ingredients:
        pool.add_task(worker, ingredient)

    pool.start()
    pool.join()
    pool.stop_threads()
    gw2db.close()

    if info:
        return pool.results
    
    return sum([d['total_cost'] for d in pool.results])

def watchlist_compute(input_file, output_file):
    '''Reads item names from input_file and writes crafting cost, tp sell price, 
    and ROI info for each item to output_file.
    Arguments: input_file, output_file'''

    # Lookup each item name in file, convert to ID, then add to list L
    gw2db = Gw2Database()
    with open(input_file) as fin:
        L = []
        for line in fin:
            item_name = line.rstrip('\n')
            item_id = gw2db.lookup(item_name)
            L.append({'item_id': item_id , 'item_name': item_name})
    
    # Create a blank file
    with open(output_file, 'w') as newfile:
        column_labels = 'name', 'craft_cost', 'sell', 'ROI'
        newfile.write('{:>35} {:>20} {:>15} {:>15}\n'.format(*column_labels))

    # Write info to file
    with open(output_file, 'a+') as fout:
        print('Writing...')
        for item_dict in L:
            craft = crafting_cost(item_dict['item_id'])
            sell = gw2api.v2_listings_sell(item_dict['item_id'])
            try: 
                # Potentially DivisionByZero Exception
                roi = int((sell-craft)/craft*100)
            except:
                roi = 0
                
            tup = item_dict['item_name'], gold(craft), gold(sell), str(roi)
            if roi > 0:
                fout.write('{:>35} {:>20} {:>15} {:>15}\n'.format(*tup))

def gold(value): #123793
    '''Returns a string representing an integer's equivalent gold value'''
    gold = value//10000
    silver = (value-gold*10000)//100
    copper = (value-gold*10000-silver*100)
    return '{}g {}s {}c'.format(gold, silver, copper)

def remove_quotes(input_file):
    L = []
    with open(input_file, 'r+') as f: 
        for line in f:
            line = line.rstrip('\n')
            line = line.strip('"')
            L.append(line)
        f.seek(0)
        f.truncate()
        for string in L:
            f.write(string + '\n')
    
if __name__ == '__main__':
    #Oiled Forged Scrap: 82796
	#Green Torch Handle recipe: 4458
	#Rough Sharpening Stone: 9431
	#Lump of Primordium: 19924
    #Gossamer Patch: 76614
    print(crafting_cost('Warbeast Greaves', info = True))



    


    

    