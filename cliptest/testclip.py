import operator
from osgeo import gdal, gdal_array, osr
import shapefile
try:
	import Image
	import ImageDraw
except:
	from PIL import Image, ImageDraw

#declares variables
raster = "stretched.tif"
shp = "pileB"
output = "mosaic_clip"

#converts python imaging lib array to gdaul_array image
def imageToArray(i):
	a = gdal_array.numpy.fromstring(i.tobytes(), 'b')
	a.shape = i.im.size[1], i.im.size[0]
	return a

#uses a gdal geomatrix (gdal.GetGeoTransform()) to calculate
def world2Pixel(geoMatrix, x, y):
	ulX = geoMatrix[0]
	ulY = geoMatrix[3]
	xDist = geoMatrix[1]
	yDist = geoMatrix[5]
	rtnX = geoMatrix[2]
	rtnY = geoMatrix[4]
	pixel = int((x - ulX) / xDist)
	line = int((ulY - y) / abs(yDist))
	return (pixel, line)

#load source data as a gdal_array 
#and load gdal image to get geotransform (world file) info
srcArray = gdal_array.LoadFile(raster)
srcImage = gdal.Open(raster)
geoTrans = srcImage.GetGeoTransform()
#pyshp opens the shp
r = shapefile.Reader("{}.shp".format(shp))
#convert layer extent to image pixel coordinates
minX, minY, maxX, maxY = r.bbox
ulX, ulY = world2Pixel(geoTrans, minX, maxY)
lrX, lrY = world2Pixel(geoTrans, maxX, minY)
#calculate the pixel size of the new img
pxWidth = int(lrX - ulX)
pxHeight = int(lrY - ulY)
clip = srcArray[:, ulY:lrY, ulX:lrX]
#create new geomatrix for the img
#to contain georeferencing data
geoTrans = list(geoTrans)
geoTrans[0] = minX
geoTrans[3] = maxY
#map pts to pixels for drawing the county boundary
#on a blank 8 big b&w mask img
pixels = []
for p in r.shape(0).points:
	pixels.append(world2Pixel(geoTrans, p[0], p[1]))
rasterPoly = Image.new("L", (pxWidth, pxHeight), 1)
#create a blank image in PIL to draw the polygon
rasterize = ImageDraw.Draw(rasterPoly)
rasterize.polygon(pixels, 0)
#convert the PIL img to a NumPy array
mask = imageToArray(rasterPoly)
#clip the img using the mask
clip = gdal_array.numpy.choose(mask, (clip, 0)).astype(
	
gdal_array.numpy.uint8)
#Save ndvi as tiff
gdal_array.SaveArray(clip, "{}.tif".format(output),
	format="GTiff", prototype=raster)




