from osgeo import gdal, osr

import numpy as np
import os

import math

from datetime import datetime

def invert_geo_transform(gt_in):
    #we assume a 3rd row that is [1 0 0]

    #Compute determinate
    det = gt_in[1] * gt_in[5] - gt_in[2] * gt_in[4];

    if abs(det) < 0.000000000000001:
        return None

    inv_det = 1.0 / det;

    #compute adjoint, and devide by determinate
    gt_out = [0,0,0,0,0,0]
    gt_out[1] =  gt_in[5] * inv_det;
    gt_out[4] = -gt_in[4] * inv_det;

    gt_out[2] = -gt_in[2] * inv_det;
    gt_out[5] =  gt_in[1] * inv_det;

    gt_out[0] = ( gt_in[2] * gt_in[3] - gt_in[0] * gt_in[5]) * inv_det;
    gt_out[3] = (-gt_in[1] * gt_in[3] + gt_in[0] * gt_in[4]) * inv_det;

    return gt_out

def apply_geotransform(geotransform, x, y):
    out_x = geotransform[0] + geotransform[1] * x + geotransform[2] * y
    out_y = geotransform[3] + geotransform[4] * x + geotransform[5] * y
    return out_x, out_y

def read_proj(filename):
    """
    Reads the contents of a projection file based on the given filename
    """
    basename, ext = os.path.splitext( filename )
    prjfile = basename + ".prj"
    if os.path.exists( prjfile ):
        f = open(prjfile)
        projection = f.read()
        f.close()
        return projection
    return None

def intersects( a, b ):
    """
    Whether two extents intersect
    """
    exclusive = a[0] >= b[2] or a[2] <= b[0] or a[1] >= b[3] or a[3] <= b[1]
    return not exclusive

def intersection( a, b ):
    """
    Computes the intersection of two extents
    """
    if not intersects(a,b):
        return None

    min_x = max(a[0], b[0])
    max_x = min(a[2], b[2])
    min_y = max(a[1], b[1])
    max_y = min(a[3], b[3])
    return (min_x, min_y, max_x, max_y)

def clamp(value, min_val, max_val):
    if value < min_val:
        return min_val
    if value > max_val:
        return max_val
    return value

def clamp_above(value, minimum):
    if value < minimum:
        return minimum
    else:
        return value

def clamp_below(value, maximum):
    if value > maximum:
        return maximum
    else:
        return value


class GDALDataset:
    def __init__(self, name, filename):
        self.filename = filename
        self.name = name

        self.ds = gdal.Open(str(filename))
        if self.ds:
            self.geotransform = self.ds.GetGeoTransform()
            self.invgeotransform = invert_geo_transform(self.geotransform)

        self.projection = self.ds.GetProjection()
        if not self.projection or len(self.projection) == 0:
            self.projection = read_proj( file )

        llx, lly = self.pixel_to_geo( 0.0, self.ds.RasterYSize)
        urx, ury = self.pixel_to_geo( self.ds.RasterXSize, 0.0)

        self.extent = (llx, lly, urx, ury)

    def pixel_to_geo( self, x, y ):
        """
        Converts pixel coordinates to geo coordinates in the local coordinate system of the file
        """
        return apply_geotransform( self.geotransform, x, y )

    def geo_to_pixel( self, x, y ):
        """
        Converts map coordinates to pixel coordinates
        """
        return apply_geotransform( self.invgeotransform, x, y )

    @property
    def bands(self):
        return self.ds.RasterCount

    @property
    def all_bands(self):
        return range(1, self.bands+1)

    @property
    def size(self):
        return (self.ds.RasterXSize, self.ds.RasterYSize)

    @property
    def geo_size(self):
        return (self.extent[2] - self.extent[0], self.extent[3] - self.extent[1])

    @property
    def pixel_size(self):
        size = self.size
        geo_size = self.geo_size
        return (geo_size[0] / size[0], geo_size[1] / size[1])

    def read_band(self, bands, xoff=0, yoff=0, win_xsize=None, win_ysize=None, buf_xsize=None, buf_ysize=None):
        """
        Reads data from a band.  Returns a numpy array with the data
        """
        try:
            # See if they passed in a list
            arrays = []
            for b in bands:
                data = self.ds.GetRasterBand( b ).ReadAsArray(xoff, yoff,
                                                              win_xsize, win_ysize,
                                                              buf_xsize, buf_ysize)
                arrays.append( data )
            return np.dstack( arrays )

        except TypeError:
            # Assume they just passed in an int and want a single band
            return self.ds.GetRasterBand( bands ).ReadAsArray(xoff, yoff, win_xsize, win_ysize, buf_xsize, buf_ysize)

    def read_extent(self, bands, extent, buf_xsize, buf_ysize):
        """
        Samples an extent from the dataset into the given bounds
        (nearest only for now)
        """
        # Compute the read window from the dataset
        inter = intersection( self.extent, extent )
        if not inter:
            print "No intersection %s: %s" % (self.extent, extent)
            return None

        min_x, max_y = self.geo_to_pixel(inter[0], inter[1])
        max_x, min_y = self.geo_to_pixel(inter[2], inter[3])
        min_x = int(math.floor( min_x ))
        min_y = int(math.floor( min_y))
        max_x = int(math.ceil( max_x ))
        max_y = int(math.ceil( max_y))

        if min_x < 0 or min_y < 0 or max_x > self.size[0] or max_y > self.size[1]:
            print "Dimensions out of range %s, %s, %s, %s" % (min_x, min_y, max_x, max_y)
            print "Size %sx%s" % (self.size[0], self.size[1])
            return None

        print "Reading bands from %s, %s, %s, %s" % (min_x, min_y, max_x, max_y)

        return self.read_band( bands,
                               xoff= min_x,
                               yoff= min_y,
                               win_xsize =max_x - min_x,
                               win_ysize= max_y - min_y,
                               buf_xsize=buf_xsize,
                               buf_ysize=buf_ysize)

class Interp:
    NEAREST = 0
    BILINEAR = 1
    AVERAGE = 2

class HeightField(object):
    def __init__( self, heights, extent ):
        self.heights = heights
        self.extent = extent

    def get_elevation_at_pixel( self, c, r, interp=Interp.AVERAGE ):
        """
        Gets the elevation at the given pixel
        """

        #print "Getting at pixel %s,%s" % (c, r)
        if c < 0 or c > self.heights.shape[0] -1 or r < 0 or r > self.heights.shape[1] -1:
            return None

        if interp == Interp.NEAREST:
            return self.heights[int(c), int(r)]
        else:
            rowMin = int(clamp(math.floor(r), 0, self.heights.shape[1] -1))
            rowMax = int(clamp(math.ceil(r) , 0, self.heights.shape[1] -1))
            colMin = int(clamp(math.floor(c), 0, self.heights.shape[0] -1))
            colMax = int(clamp(math.ceil(c) , 0, self.heights.shape[0] -1))

            if rowMin > rowMax: rowMin = rowMax;
            if colMin > colMax: colMin = colMax;

            llHeight = self.heights[colMin, rowMin]
            ulHeight = self.heights[colMin, rowMax]
            lrHeight = self.heights[colMax, rowMin]
            urHeight = self.heights[colMax, rowMax]

            #print "Averaging %s, %s, %s, %s" % (llHeight, ulHeight, lrHeight, urHeight)

            #if not isValidValue(urHeight, band) or not isValidValue(llHeight, band) or not isValidValue(ulHeight, band) or not isValidValue(lrHeight, band):
            #    return NO_DATA_VALUE;


            if interp == Interp.BILINEAR:
                if ((colMax == colMin) and (rowMax == rowMin)):
                    #Exact match
                    result = llHeight
                elif colMax == colMin:
                    #Linear interpolate vertically
                    result = (float(rowMax) - r) * llHeight + (r - float(rowMin)) * ulHeight
                elif rowMax == rowMin:
                    #Linear interpolate horizontally
                    result = (float(colMax) - c) * llHeight + (c - float(colMin)) * lrHeight
                else:
                    #Bilinear interpolate
                    r1 = (float(colMax) - c) * llHeight + (c - float(colMin)) * lrHeight
                    r2 = (float(colMax) - c) * ulHeight + (c - float(colMin)) * urHeight
                    result = (float(rowMax) - r) * r1 + (r - float(rowMin)) * r2
            elif interp == Interp.AVERAGE:
                x_rem = c - int(c)
                y_rem = r - int(r)

                w00 = (1.0 - y_rem) * (1.0 - x_rem) * llHeight;
                w01 = (1.0 - y_rem) * x_rem * lrHeight;
                w10 = y_rem * (1.0 - x_rem) * ulHeight;
                w11 = y_rem * x_rem * urHeight;

                result = (w00 + w01 + w10 + w11);

        return result


    def get_elevation_at_location( self, x, y, interp=Interp.AVERAGE ):
        """
        Gets the elevation at the given location
        """
        x_interval = (self.extent[2] - self.extent[0]) / float(self.heights.shape[0] - 1)
        y_interval = (self.extent[3] - self.extent[1]) / float(self.heights.shape[1] - 1)
        px = (float(x) - self.extent[0]) / x_interval
        py = (float(y) - self.extent[1]) / y_interval
        return self.get_elevation_at_pixel( px, py )
