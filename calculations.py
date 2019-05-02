from database import Gw2Database
from gw2api import v2_listings_buy, v2_listings_sell
import threading
import os

def worker(item_id, count, result_list):
    gw2db = Gw2Database()
    
    # Check database for vendor entry, then buy, then sell, else default to 0
    unit_cost = gw2db.vendor_price(item_id)
    if unit_cost == 0:
        unit_cost = v2_listings_buy(item_id)
        if unit_cost == 0:
            unit_cost = v2_listings_sell(item_id) 
   
    keys = ('item_id', 'item_name', 'count', 'unit_cost', 'total_cost')
    values = (item_id, gw2db.lookup(item_id), count, unit_cost, unit_cost*count)
    result_list.append(dict(zip(keys,values)))

def material_cost(item_id, *args):
    gw2db = Gw2Database()
    ingredients = gw2db.base(item_id)
    result_list = [] 
    
    threads_list = []
    for ing in ingredients:
        th = threading.Thread(target = worker, args = (ing['item_id'], ing['count'], result_list))
        th.start()
        threads_list.append(th)
    for th in threads_list:
        th.join()
    
    if 'info' in args:
        return result_list
    
    return sum([ing['total_cost'] for ing in result_list])

if __name__ == '__main__':
    #Oiled Forged Scrap: 82796
	#Green Torch Handle recipe: 4458
	#Rough Sharpening Stone: 9431
	#Lump of Primordium: 19924
    #Gossamer Patch: 76614
    
    os.chdir('E:\Desktop2\Python Projects\gw2_code')
    from utilities.log import Log
    
    gw2db = Gw2Database()
    output = Log('rune_prices.txt') 
    with open('runes.txt') as f:
        for line in f:
            item_name = line.rstrip('\n')
            cost = material_cost(gw2db.lookup(item_name))
            sell = v2_listings_sell(gw2db.lookup(item_name))
            try:
                roi = int((sell-cost)/cost *100)
            except:
                roi = 0
            if roi <= 0:
                continue
            tup = (item_name, str(cost), str(sell), str(roi)) # Could be a bit less verbose
            output.write(('{:>50} {:>15} {:>15} {:>15}'.format(*tup)))
            

   
    # name = 'Superior Rune of the Berserker'
    # cost = material_cost(name)
    # sell = v2_listings_sell(gw2db.lookup(name))
    
    # x = name, cost, sell
    # print(x)
    # # Outputs to text file in column form
        # Name, Material Cost, TP Sell Price, ROI
        

        

    


    
    
    
    