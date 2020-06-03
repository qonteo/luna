from PIL import Image
import PIL
import io


def checkFormatAndConvertImage(byteImg):
    """
    Check format mimetype and image conversion, if format is not ["image/jpg", "image/jpeg", " image/pjpeg"]

    :param byteImg: byte image.
    :return: converted byte image.
    """
    img = Image.open(io.BytesIO(byteImg))
    if img.format == 'JPEG':
        return byteImg
    else:
        output = io.BytesIO()
        img.convert('RGB').save(output, format = 'JPEG')
        return output.getvalue()


def resizeImage(binImage, maxSize):

    img = Image.open(io.BytesIO(binImage))
    width, height = img.size
    ratio = min(maxSize / width, maxSize / height)
    size = int(width * ratio), int(height * ratio)
    resizeImg = img.resize(size, PIL.Image.BILINEAR)
    output = io.BytesIO()
    resizeImg.save(output, format = 'JPEG')
    return output.getvalue()