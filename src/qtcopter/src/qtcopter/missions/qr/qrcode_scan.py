#!/usr/bin/env python

'''
Continously scan for qrcodes from a webcam with zbar

> qrcode_scan.py [cam id]

vasily & roee
03/2015
'''
import sys
import cv2
import cv
import zbar
from PIL import Image
import numpy
import time


CAM = 0
WINDOW = 'bah'

def find_qrcodes(img, width, height):
    " scan a cv2 image with zbar "
    # TODO: how to get width & height from img?
    
    # convert to zbar image
    # TODO: how to directly convert cv2 image to zbar image?
    img_rgb = img #cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    PIL_img = Image.fromarray(img_rgb).convert('L')
    #img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    zbar_img = zbar.Image(width, height, 'Y800', PIL_img.tostring())

    # create scanner object
    scanner = zbar.ImageScanner()
    # TODO: how to only scan QRCodes?
    scanner.parse_config('enable')

    # scan
    results = scanner.scan(zbar_img)
    # results holds number of results..
    
    return list(zbar_img)

def is_grayscale(img):
    return len(img.shape) == 2

def loop(camid=CAM):
    # open camera
    # TODO: check if this works for video files
    cam = cv2.VideoCapture(camid)
    if not cam.isOpened():
        print 'Could not open camera', camid
        sys.exit(-1)
        
    # get video size
    width = int(cam.get(cv.CV_CAP_PROP_FRAME_WIDTH))
    height = int(cam.get(cv.CV_CAP_PROP_FRAME_HEIGHT))

    t = time.time()
    all_time = 1
    cam_time = 1
    zbar_time = 1
    # loop..
    while True:
        all_time = time.time()-t
        print 'all: %.3fs % 3.0ffps cam: %.3fs %4.0ffps zbar: %.3fs %4.0ffps' %\
		(all_time, 1./all_time, cam_time, 1./cam_time, zbar_time, 1./zbar_time)
        t = time.time()
        # grab frame
        ret, img = cam.read()
        cam_time = time.time()-t
        if not ret:
            print 'could not grab frame'
            cam.release()
            sys.exit(-2)
        t2 = time.time()
        results = find_qrcodes(img, width, height)
        zbar_time = time.time()-t2
        for res in results:
            print '%s %s: %r' % (time.ctime(), res.type, res.data)
            #print 'decoded type=%s q=%r loc=%r %r' % (res.type, res.quality, res.location, res.data)

            # draw a rectangle around found qrcodes
            poly1 = numpy.array(res.location, numpy.int32).reshape(-1,1,2)
            polys = [poly1]
            if is_grayscale(img):
                cv2.polylines(img, polys, True, 255)
            else:
                cv2.polylines(img, polys, True, (0, 0, 255))
        
        # show stream
        cv2.imshow(WINDOW, img)
        # show picture for minimal time
        if cv2.waitKey(1) == ord('q'):
            break

    cv2.destroyWindow(WINDOW)
    cam.release()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        cam = sys.argv[1]
    else:
        cam = None
        
    # try converting to integer
    try:
        cam = int(cam)
    except:
        pass

    # run loop
    if cam is not None:
        rc = loop(cam)
    else:
        rc = loop()

    sys.exit(rc)
