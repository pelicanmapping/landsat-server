from scenelist import SceneList
import tornado.escape
import tornado.ioloop
import tornado.web

from PIL import Image
from tile import Profile, Tile

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

import numpy as np
import os

import sys

scene_list = None

profile = Profile()

class Cache(object):
    def __init__(self, path):
        self.path = path

    def get_key( self, layer, x, y, z):
       return os.path.join(self.path, "%s/%s/%s/%s.npy" % (layer,z,x,y))

    def get(self, layer, x, y, z):
       key = self.get_key( layer, x, y, z)
       if os.path.exists( key ):
          return np.load( key )
       return None

    def set( self, layer, x, y, z, data ):
       key = self.get_key( layer, x, y, z)
       dirname = os.path.dirname( key )
       if not os.path.exists( dirname ):
           try:
               os.makedirs( dirname  )
           except OSError:
               pass
       np.save(key, data)

cache = Cache("cache")

def get_tile(layer, tile):
    global cache
    data = cache.get(layer.name, tile.x, tile.y, tile.z)
    #data = None
    if data is None:
        #print "Cache miss"
        size=256
        print "Reading data from %s %s %s" % (layer.name, layer.all_bands, tile.bounds)
        data = layer.read_extent(layer.all_bands, tile.bounds, size, size )
        if data is not None:
            cache.set(layer.name, tile.x, tile.y, tile.z, data )
    else:
        #print "Cache hit"
        pass
    return data

def save_array(data, ext):
    image = Image.fromarray(data)

    if ext == "png":
        output = StringIO.StringIO()
        image.save(output, "PNG")
        contents = output.getvalue()
        return contents, "image/png"
    elif ext == "jpg" or ext == "jpeg":
        output = StringIO.StringIO()
        image.save(output, "JPEG")
        contents = output.getvalue()
        return contents, "image/jpeg"
    elif ext == "tif" or ext == "tiff":
        output = StringIO.StringIO()
        image.save(output, "tiff")
        contents = output.getvalue()
        return contents, "image/tiff"
   
class TileHandler(tornado.web.RequestHandler):

    def get(self, z, x, y, ext):
        if int(z) < 8:
            print "Returning 404 for %s,%s,%s" % (z, x, y)
            self.set_status(404)
            self.finish()
            return

        print "Processing tile %s,%s,%s" % (z,x,y)

        tile = profile.get_tile(int(z), int(x), int(y) )

        # Now find the first scene that intersects this tile
        scene = scene_list.select_scene(tile)
        if not scene:
            print "Couldn't find scene"
            self.set_status(400)
            self.finish()
            return

        scene.ensure_local()
        data = get_tile( scene.dataset, tile )
        if data is None:
            print "Couldn't read data"
            self.set_status(400)
            self.finish()
            return
        #print "Got data shape %s"
        
        # It's the raw 432 data in that order so scale it and return it
        result = data * 255.0/30000.0
        #result[:,:,3] *= .8
        result = np.array(result, dtype=np.uint8)
        contents, content_type = save_array(result, ext)
        self.set_header("Content-Type", content_type)
        self.set_header("Access-Control-Allow-Origin", "*")
        self.write(contents)
        self.finish()

class StatusHandler(tornado.web.RequestHandler):

    def get(self):
        self.write("Hi there")
        self.finish()

class TMSHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.finish()

application = tornado.web.Application([
    (r"/index.html", StatusHandler),
    #(r"/tiles/tilemapresource.xml", TMSHandler),
    (r"/tiles/([0-9]+)/([0-9]+)/([0-9]+).(.+)", TileHandler),
])

if __name__ == "__main__":
    scene_filename = "scene_list.csv"
    scene_list = SceneList(scene_filename)
    print "Loaded %s scenes" % len(scene_list.scenes)
    port = 8000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    print "Listening on port %s" % port
    application.listen(port)
    tornado.ioloop.IOLoop.instance().start()

    
