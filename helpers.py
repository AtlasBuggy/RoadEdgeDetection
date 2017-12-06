# Most of this is fairly inefficient and would benefit from basic optimization.
# Check this out for optimization:
# https://stackoverflow.com/questions/32328179/opencv-3-0-python-lineiterator

# Like-color code:
# https://stackoverflow.com/questions/44428315/similar-color-detection-in-python

# Takes an image and 2 points on the image
# Designed to take something closer to vertical than to horizontal
# Returns a "histogram" of the pixels on the line between p0 and p1
def linehist(img, p0, p1):
    x0, y0 = p0
    x1, y1 = p1
    dx = x1 - x0
    dy = y1 - y0

    if dy == 0:
        return None

    slope = float(dx)/float(dy) # since we'll iterate over y

    minA = minB = minC = 256
    maxA = maxB = maxC = -1
    As = 256*[0]
    Bs = 256*[0]
    Cs = 256*[0]
    numpix = 0

    x = float(x0)
    deltay = 1 if y0 < y1 else -1

    for y in range(y0, y1+1, deltay):
        a = img[y,int(x)][0]
        b = img[y,int(x)][1]
        c = img[y,int(x)][2]
        if a < minA:
            # As = (minA-a)*[0] + As
            minA = a
        elif a > maxA:
            # As += (a-maxA)*[0]
            maxA = a
        if b < minB:
            minB = b
        elif b > maxB:
            maxB = b
        if c < minC:
            minC = c
        elif c > maxC:
            maxC = c
        As[a]+=1
        Bs[b]+=1
        Cs[c]+=1
        numpix += 1

        x += slope*deltay
    return ((As, minA, maxA), (Bs, minB, maxB), (Cs, minC, maxC), numpix)

# Find the mean of each channel (eg BGR or HSV) in img
def meanline(img, p0, p1):
    if p0[1] == p1[1]:
        return (0,0,0)

    sumA = sumB = sumC = 0
    ((As,minA,maxA),(Bs,minB,maxB),(Cs,minC,maxC),numpix) = linehist(img,p0,p1)

    for i in range(0, 255):
        sumA += i*As[i]
        sumB += i*Bs[i]
        sumC += i*Cs[i]

    return (int(sumA/numpix),int(sumB/numpix),int(sumC/numpix))

# Takes 2 points that define a line that crosses shape
# Returns 2 points on the same line that are both in the shape
# If a point is already in the shape, it doesn't move,
# but if it's outside it is brought to the nearest edge.
def makeinrange(shape, p0, p1):
    rows, cols, channels = shape
    x0, y0 = p0
    x1, y1 = p1
    dx = x1 - x0
    dy = y1 - y0
    slope = float(dx)/float(dy)

    if x0 < 0:
        y0 = y0 + int(float(0-x0)/slope)
        x0 = 0
    if x1 < 0:
        y1 = y1 + int(float(0-x1)/slope)
        x1 = 0
    if y0 < 0:
        x0 = x0 + int(float(0-y0)*slope)
        y0 = 0
    if y1 < 0:
        x1 = x1 + int(float(0-y1)*slope)
        y1 = 0

    if x0 > cols-1:
        y0 = y0 + int(float((cols-1) - x0)/slope)
        x0 = cols-1
    if x1 > cols-1:
        y1 = y1 + int(float((cols-1) - x1)/slope)
        x1 = cols-1
    if y0 > rows-1:
        x0 = x0 + int(float((rows-1) - y0)*slope)
        y0 = rows-1
    if y1 > rows-1:
        x1 = x1 + int(float((rows-1) - y1)*slope)
        y1 = rows-1

    return ((x0,y0),(x1,y1))
