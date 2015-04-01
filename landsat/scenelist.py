import os
import subprocess

cache_path = "/data/landsat8_temp"

from layer import GDALDataset

class Scene:
    def __init__(self, entity_id, acquisition_date, cloud_cover, processing_level, path, row, min_lat, min_lon, max_lat, max_lon, download_url):
        self.entity_id = entity_id
        self.acquisition_date = acquisition_date
        self.cloud_cover = float(cloud_cover)
        self.processing_level = processing_level
        self.path = int(path)
        self.row = int(row)
        self.min_lat = float(min_lat)
        self.min_lon = float(min_lon)
        self.max_lat = float(max_lat)
        self.max_lon = float(max_lon)
        self.bounds = (self.min_lon, self.min_lat, self.max_lon, self.max_lat)   
        self.download_url = download_url.replace("\n", "")
        self.root_url = self.download_url.rstrip("/index.html")
        self.s3_root = self.root_url.replace("https://s3-us-west-2.amazonaws.com/landsat-pds", "s3://landsat-pds")
        self.vrt = os.path.join(cache_path, "%s.vrt" % self.entity_id)
        self.dataset = None

    def ensure_local(self):
        if not os.path.exists(self.vrt):
            # Download the files from AWS
            bands = [4,3,2]
            for b in bands:
                filename = "%s_B%s.TIF" % (self.entity_id, b)
                src = self.root_url + "/" + filename
                src_s3 = self.s3_root + "/" + filename 
                dest = os.path.join(cache_path, filename)
                print "Downloading %s to %s" % (src, dest)
                os.system('wget "%s" -O %s' % (src, dest))
                #os.system("aws s3 cp %s %s" % (src_s3, dest))
                        
            merged_vrt = os.path.join(cache_path, "%s_merged.vrt" % self.entity_id)
            cmd = [
                "gdalbuildvrt",
                "%s" % merged_vrt,
                "-separate"
            ]
            for b in bands:
                filename = "%s_B%s.TIF" % (self.entity_id, b)
                dest = os.path.join(cache_path, filename)
                cmd.append( dest )
            subprocess.call(cmd)

            # Now warp the VRT
            cmd = [
                "gdalwarp",
                "-of", "VRT",
                "-t_srs", "epsg:4326",
                "-r", "bilinear",
                "%s" % merged_vrt,
                "%s" % self.vrt
            ]
            subprocess.call(cmd)
        if not self.dataset:
            self.dataset = GDALDataset(self.entity_id, self.vrt)



class SceneList:
    def __init__(self, filename):
        self.filename = filename
        self.scenes = []
        with open(filename) as f:
            lines = f.readlines()
            for l in lines[1:]:
                parts = l.split(",")
                self.scenes.append(Scene(parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], parts[6], parts[7], parts[8], parts[9], parts[10] ))

    def select_scene(self, tile):
        
        #for s in self.scenes:
        #    if tile.intersects(s.bounds):
        #        return s
        result = None
        for s in self.scenes:
            if tile.intersects(s.bounds) and s.cloud_cover >= 0.0:
                if not result:
                    result = s
                else:
                    if s.cloud_cover < result.cloud_cover:
                        result = s
        return result  
        #return None

