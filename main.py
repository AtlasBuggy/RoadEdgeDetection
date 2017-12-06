import cv2
import numpy as np
from matplotlib import pyplot as plt
import helpers as h
import scanline

cap = cv2.VideoCapture("ascension0.avi")
_, f0 = cap.read()
height , width , layers = f0.shape

# Bounds on the frame when we crop
# For left line detection
lxlo = 0
lxhi = 300
lylo = 130
lyhi = 320
# For right line detection
rxlo = 370
rxhi = 640
rylo = 130   # top edge
ryhi = 320   # bottom edge

flo = 1500  # frame count bounds
fhi = 3500

# Theta bounds
# For left line detection
ltlo = 0.5
lthi = 1.1
# For right line detection
rtlo = 2.1
rthi = 2.6

# Distance from the detected line to the parallel scan lines
# These are used to detect whether the line is a curb
# If one has high saturation and the other low,
# the line is the curb (on that side) because grass has higher sat than road
sidelinedist = 75

# Length and number of the horizontal scan lines
# These are used to differentiate the yellow line from other road features
# A yellow line will have a large spike in saturation,
# while the white and tar lines won't
stripelen = 60
numstripes = 20

# These are parameters that scanline takes in
stripefiltersize = 11 # odd is good
stripesatcutoff = 65  # 70 works pretty well for double line detection
                      # 60 works better for finding 1+ lines


# Write the output to out.avi
vid = cv2.VideoWriter("out.avi",cv2.VideoWriter_fourcc('H','2','6','4'),30,
                      (lxhi-lxlo + rxhi-rxlo, lyhi-lylo))

font = cv2.FONT_HERSHEY_SIMPLEX

# Returns true if the line has an angle that matches what we're expecting
def isgoodline(line, tlo, thi):
    rho, theta = line[0]
    return tlo < theta < thi

# The real stuff
def do_shit(frame,xlo,xhi,ylo,yhi,tlo,thi):
    # Crop so that we don't have the buggy or horizon
    cutframe = frame[ylo:yhi, xlo:xhi]
    hsv = cv2.cvtColor(cutframe, cv2.COLOR_BGR2HSV)

    # Detect edges
    # TODO: Tweak all the parameters
    edges = cv2.Canny(cutframe,50,150,apertureSize = 3)
    lines = cv2.HoughLines(edges,1,np.pi/180,90) # 90 is the min line length

    # lines is a list of detected lines in order of how well they fit the image

    if(lines is not None):
        # Get the first line that is at a reasonable angle
        goodline = next((line for line in lines if isgoodline(line,tlo,thi)), None)

        if goodline is not None:
            # Convert from kind of polar format to cartesian
            rho, theta = goodline[0]
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a*rho
            y0 = b*rho
            # This looks pretty hacky - probably should do something better
            x1 = int(x0 + 1000*(-b))
            y1 = int(y0 + 1000*(a))
            x2 = int(x0 - 1000*(-b))
            y2 = int(y0 - 1000*(a))
            p1, p2 = h.makeinrange(cutframe.shape, (x1,y1), (x2,y2))
            p1x, p1y = p1
            p2x, p2y = p2

            # Get points for the parallel scan lines
            lp1, lp2 = h.makeinrange(cutframe.shape,
                                     (x1-sidelinedist,y1),(x2-sidelinedist,y2))
            rp1, rp2 = h.makeinrange(cutframe.shape,
                                     (x1+sidelinedist,y1),(x2+sidelinedist,y2))

            # Get the avg H, S, and V for the parallel scan lines
            # Currently, we only use saturation
            huel, satl, vall = h.meanline(hsv, lp1, lp2)
            huer, satr, valr = h.meanline(hsv, rp1, rp2)

            # Count how many stripes we test and how many have yellow lines
            stripecount = 0
            yellowstripecount = 0

            for stripei in range(numstripes):
                curx = int(p1x + (p2x-p1x)*stripei/numstripes)
                cury = int(p1y + (p2y-p1y)*stripei/numstripes)

                if curx - stripelen >= 0 and curx + stripelen < xhi-xlo:
                    # Get the array of pixels that we're scanning
                    ps = hsv[cury:cury+1, (curx-stripelen):(curx+stripelen)][0]

                    # Count the number of left edges in the sat channel
                    scancount,_,_ = scanline.countedges(ps,
                                                        stripefiltersize,
                                                        stripesatcutoff)
                    stripecount += 1

                    # if scancount = 0, it's pry white/tar
                    # if scancount > 2, it's pry curb
                    if scancount == 1 or scancount == 2:
                        yellowstripecount += 1

            # The "probability" that this stripe is yellow
            probyellow = (yellowstripecount / stripecount
                          if stripecount > 4 # we don't want to use this
                          else 0.0)          # with few samples

            ### Draw the main line we detected
            cv2.line(cutframe,p1,p2,(0,0,255),1)

            ### Draw the parallel lines and their avg saturations
            # cv2.line(cutframe,lp1,lp2,(0,0,255),1)
            # cv2.line(cutframe,rp1,rp2,(0,0,255),1)
            # cv2.putText(cutframe, str(vall),(50,15),
            #             font,0.5,(255,0,0), 1, cv2.LINE_AA)
            # cv2.putText(cutframe, str(valr),(50,35),
            #             font,0.5,(255,0,0), 1, cv2.LINE_AA)


            ### Draw the horizontal stripes
            # for linei in range(2*stripelen):
            #     linex = xp-stripelen+linei
            #     cutframe[yp+2,linex] = edgeline[linei]
            #     cutframe[yp+1,linex] = satline[linei]
            # cv2.line(cutframe, (xp-stripelen,yp), (xp+stripelen,yp), (255,0,0),1)

            ### Draw the yellow-line probability
            # cv2.putText(cutframe, str(probyellow),(100,70),
            #             font,0.5,(255,0,0), 1, cv2.LINE_AA)

            ### Make a guess at which feature it is
            # From some experimentation, when at the left curb,
            # the lowest satl is around 70, highest satr is around 40
            if satl - satr > 30:
                cv2.putText(cutframe, "LEFT SIDE",(100,100),
                            font,0.5,(255,0,0), 1, cv2.LINE_AA)

            elif satr - satl > 30:
                cv2.putText(cutframe, "RIGHT SIDE",(100,100),
                            font,0.5,(255,0,0), 1, cv2.LINE_AA)

            elif probyellow > 0.69:
                cv2.putText(cutframe, "YELLOW",(100,100),
                            font,0.5,(255,0,0), 1, cv2.LINE_AA)

            # This is either white, tar, or yellow at the far edge
            else:
                cv2.putText(cutframe, "WHITE",(100,100),
                            font,0.5,(255,0,0), 1, cv2.LINE_AA)


            ### Display the x-value of the detected line at y = 50
            linex = p1x + (p2x - p1x)/(p2y - p1y)*(50 - p1y)
            cv2.putText(cutframe, str(linex),(200,100),
                        font,0.5,(255,0,0), 1, cv2.LINE_AA)

            ### Display the distance from corner to line (?)
            # cv2.putText(cutframe, ,(200,100),
            #             font,0.5,(255,0,0), 1, cv2.LINE_AA)

            ### Draw the frame number
            cv2.putText(cutframe, str(i),(0,15),
                        font,0.5,(0,0,255), 1, cv2.LINE_AA)

    return cutframe


# Drop the frames we don't want
for i in range(0,flo):
    cap.grab()

# Control loop?
for i in range(flo,fhi):
    frameread, frame = cap.read()

    if not frameread:
        break

    loutframe = do_shit(frame,lxlo,lxhi,lylo,lyhi,ltlo,lthi)
    routframe = do_shit(frame,rxlo,rxhi,rylo,ryhi,rtlo,rthi)
    together = np.concatenate((loutframe, routframe), axis=1)
    vid.write(together)

vid.release()
