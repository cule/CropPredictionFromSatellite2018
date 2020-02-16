import descarteslabs as dl
import argparse
import subprocess
# I find I need to do the import like this, from same directory:
from compute_ndvi_forCloud import tile_function

def get_dltiles(): 
    vlen=992
    padding = 16
    res = 120.0
    
    """ get a list of dltiles['features']"""
    matches=dl.places.find('north-america_united-states')
    aoi = matches[0]
    shape = dl.places.shape(aoi['slug'], geom='low')
    
    dltiles= dl.raster.dltiles_from_shape(res, vlen, padding, shape)

    return dltiles

def main(args):
    """run the tasks, with check for what's already done"""

    dltiles= get_dltiles()

    if args.dontcheck:
        done = list() #set()
    else:
        path = 'gs://lillian-bucket-storage/data'
        filelist = subprocess.check_output('gsutil ls %s/*.json'
                                           % path, shell=True).splitlines()
        done = {f.split('/')[-1].split('_')[0] for f in filelist}

    print( type(dltiles['features']), len(dltiles['features']), type(done), len(done) )
  #  print('running %d of %d tiles' % (len(dltiles['features']) -len(done)), len(dltiles))
    
    # fire off the tasks
  #  for tile in sorted(dltiles['features'] - done):
    for tile in range(len(dltiles['features'])):
        tile_function.apply_async([dltiles['features'][tile]], queue='myQueue')

    
# we make the module executable, with optional command-line arguments
# example: python run_tasks -sleeptime 50 --dontcheck
if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('-arraysize', type=int, default=100000,
                        help='make an array of this size')
    parser.add_argument('-sleeptime', type=int, default=100,
                        help='sleep this many seconds')
    parser.add_argument('--dontcheck', action='store_const', const=True,
                        default=False, help="don't check for done tasks")
    args = parser.parse_args()

    main(args)
