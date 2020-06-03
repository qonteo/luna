import os.path


def getAbsPathToFile(relativityPathToFile):
    """
    convert relativity path to resource file to absolute

    :param relativityPathToFile: relativity path
    :return: absolute path
    """
    currentDir = os.path.dirname(__file__)
    return "{}/{}".format(currentDir, relativityPathToFile)


standardImage = getAbsPathToFile("./data/Claudia_Schiffer.jpg")

glassesImage = getAbsPathToFile("./data/Glasses.jpg")
sunGlassesImage = getAbsPathToFile("./data/SunGlasses.jpg")

shortPersonList = [
    getAbsPathToFile("./data/Claudia_Schiffer_2.jpg"),
    getAbsPathToFile("./data/Claudia_Schiffer_3.jpg"),
    getAbsPathToFile("./data/Claudia_Schiffer_4.jpg"),
    getAbsPathToFile("./data/Claudia_Schiffer_5.jpg")
]

onePersonList = shortPersonList + [
    getAbsPathToFile("./data/Claudia_Schiffer_6.jpg"),
    getAbsPathToFile("./data/Claudia_Schiffer_7.jpg")
]

differentFormatList = [
    {"Content-Type": "image/bmp", "image": getAbsPathToFile("./data/Cruz.bmp")},
    {"Content-Type": "image/x-portable-pixmap", "image": getAbsPathToFile("./data/Cruz.ppm")},
    {"Content-Type": "image/tiff", "image": getAbsPathToFile("./data/Cruz.tif")},
    {"Content-Type": "image/gif", "image": getAbsPathToFile("./data/Cruz.gif")},
    {"Content-Type": "image/png", "image": getAbsPathToFile("./data/Cruz.png")}
]

rawDescriptor = {"Content-Type": "application/x-vl-face-descriptor", "image": getAbsPathToFile("./data/Claudia_Shciffer_Descriptor.bin")}

xpkFile = {"Content-Type": "application/x-vl-xpk", "image": getAbsPathToFile("./data/some_xpk.xpk")}

base64Files = [
    {"Content-Type": "image/x-bmp-base64", "filename": getAbsPathToFile("./data/Cruz_base64_bmp.txt")},
    {"Content-Type": "image/x-portable-pixmap-base64", "filename": getAbsPathToFile("./data/Cruz_base64_ppm.txt")},
    {"Content-Type": "image/x-tiff-base64", "filename": getAbsPathToFile("./data/Cruz_base64_tif.txt")},
    {"Content-Type": "image/x-gif-base64", "filename": getAbsPathToFile("./data/Cruz_base64_gif.txt")},
    {"Content-Type": "image/x-png-base64", "filename": getAbsPathToFile("./data/Cruz_base64_png.txt")},
    {"Content-Type": "image/x-jpeg-base64",
     "filename": getAbsPathToFile("./data/Claudia_Schiffer_warp_base64_jpg.txt")},
    {"Content-Type": "application/x-vl-xpk-base64", "filename": getAbsPathToFile("./data/some_xpk_base64_xpk.txt")},
    {"Content-Type": "application/x-vl-face-descriptor-base64",
     "filename": getAbsPathToFile("./data/Claudia_Shciffer_Descriptor_base64_bin.txt")}]

warpedImage = getAbsPathToFile("./data/Claudia_Schiffer_warp.jpg")
exifWarpedImage = getAbsPathToFile("./data/Claudia_Schiffer_warp_exif.jpg")

severalFaces = getAbsPathToFile("./data/several_faces.jpg")
moreThan64Faces = getAbsPathToFile("./data/more_than_64_faces.jpg")
noFaces = getAbsPathToFile("./data/no_faces.jpg")

lowImageSize = getAbsPathToFile("./data/low_size.jpg")
largeImageSize = getAbsPathToFile("./data/large_size.jpg")
