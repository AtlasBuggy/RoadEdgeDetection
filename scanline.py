import cv2

# Takes a 1-D array of pixels and counts left edges based on saturation
def countedges(ps, filtersize, satcutoff):

    # List of bits. 1 = high sat, 0 = low sat
    bi = list(map(lambda hsv: 1 if hsv[1] > satcutoff else 0, ps))

    # Provides a good visual demo of where the detected edges are
    edgeline = list(map(lambda _: [255,255,255], ps))
    # Provides a good visual demo of what has high saturation
    satline = list(map(lambda b: [255,255,255] if b == 0 else [0,0,0], bi))

    # TODO: Optimize
    numedges = 0
    for i in range(filtersize//2, len(ps) - filtersize//2):
        b0 = b1 = 0

        # Count the number of high sat pixels in a "blur" of length filtersize
        for j in range(-filtersize//2, filtersize//2):
            b0 += bi[i+j]
            b1 += bi[i+j+1]

        # If we got more than half in the right blur
        # and less than half in the left blur,
        # then we found an edge!
        if (round(b0/filtersize) < round(b1/filtersize)):
            numedges += 1
            edgeline[i] = [0,0,0]

    return numedges, edgeline, satline
