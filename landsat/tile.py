class Profile(object):
    def __init__(self, wide=2, high=1, bounds=(-180,-90,180,90)):
        self.wide = wide
        self.high = high
        self.bounds = bounds
        
    def get_num_tiles( self, lod ):
        pow2 = pow(2.0, lod)
        return (self.wide * pow2, self.high * pow2)        
        
    def get_tile_size( self, lod ):
        width = float(self.bounds[2] - self.bounds[0]) / self.wide
        height = float(self.bounds[3] - self.bounds[1]) / self.high
        pow2 = pow(2.0, lod)
        return (width/pow2, height/pow2)
        
    def get_tile( self, lod, x, y ):
        extents = self.get_tile_size( lod )
        min_x = self.bounds[0] + extents[0] * float(x)
        min_y = self.bounds[1] + extents[1] * float(y)
        max_x = min_x + extents[0]
        max_y = min_y + extents[1]
        bounds = ( min_x, min_y, max_x, max_y)
        return Tile( z=lod, x=x, y=y, bounds=bounds)                
        
        

class Tile(object):
    """
    A node in a quadtree
    """
    def __init__(self, z=0, x=0, y=0, bounds=(-180,-90,180,90)):
        self.z = z
        self.x = x
        self.y = y
        self.bounds = bounds     
        
    def __str__(self):
        return "%s (%s,%s)" % (self.z, self.x, self.y)
        
    @property
    def width(self):
        return self.bounds[2] - self.bounds[0]
        
    @property
    def height(self):
        return self.bounds[3] - self.bounds[1]      

    def intersects(self, bounds):
        """
        Whether or not this tile intersects the given bounds
        """
        b = self.bounds
        return max(b[0], bounds[0]) <= min(b[2], bounds[2]) and max(b[1], bounds[1]) <= min(b[3], bounds[3])             
                                  
    def create_child(self, quadrant ):
        width  = self.width / 2.0
        height = self.height / 2.0
        xmin = self.bounds[0]
        ymin = self.bounds[1]
        z = self.z + 1
        x = self.x * 2
        y = self.y * 2
                                      
        if quadrant == 1:
            x += 1
            xmin += width
        elif quadrant == 2:
            y += 1
            ymin += height
        elif quadrant == 3:
            x += 1
            y += 1
            xmin += width
            ymin += height
                        
        return Tile(z=z, x=x, y=y, bounds=(xmin, ymin, xmin + width, ymin + height))                                         
        

        
        
        
