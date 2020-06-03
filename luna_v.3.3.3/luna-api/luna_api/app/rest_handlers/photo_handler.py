from tornado import gen, web

from app.common import GETTER_PORTRAITS_PLUGINS
from app.rest_handlers.storage_handlers import StorageHandler
from crutches_on_wheels.utils.timer import timer
from configs.config import SEND_TO_LUNA_IMAGE_STORE
from crutches_on_wheels.errors.errors import Error
from app.functions import convertDateTime


class PhotoHandler(StorageHandler):
    """
    Handler to receive images for extract. To work with handler you must authorize and account must be active
    """

    @StorageHandler.requestExceptionWrap
    @timer
    @gen.coroutine
    def post(self):
        """
        Request for descriptor extraction from photo.  Request is forwarded to LUNA, so input parameters are the same.
        After extraction all descriptors are added to database, answer from LUNA is received
        (if other is not set in parameters).

        .. http:post:: /storage/descriptors?estimate_attributes=1&estimate_quality=1&quality_threshold=1&warped_image=1&extract_descriptor=1&extract_exif=1 

            :optparam estimate_attributes: Whether to estimate face attributes from the image.
             
             The attributes are stored in attributes object per face. Type: boolean, default: false.

            :optparam estimate_emotions: Whether to estimate emotions from the image.
             
            :optparam quality_threshold: Whether to estimate face image quality from the image. The estimated quality
                                         value is a floating point probability in [0..1] range.
            
            The quality is stored in quality parameter per face. See also quality_threshold. Type: boolean, default:
            false.
             
            :optparam estimate_quality: If estimate_quality parameter is set to 1, it is possible to apply a threshold
                                        check to each estimation. All face detections with quality below the threshold
                                        will be ignored and no descriptors will be extracted out of them. The function
                                        will proceed as usual with all the remaining detections (if left).
             
            :optparam warped_image: Whether input image is a warped or arbitrary one. Exact image warping algorithm
                                    is proprietary and this flag is intended for VisionLabs front-end tools.


             The warped image has the following properties:
              
              * it's size is always 250x250 pixels

              + it's always in RGB color format

              + it always contains just a single face

              + the face is always centered and rotated so that imaginary line between the eyes is horizontal.
             
             Type: boolean, default: false.
             
            :optparam extract_descriptor: Whether to extract face descriptor(s). Useful when face descriptor is not
                                          actually required and only face detection bounding rectangle (with optional
                                          attributes and quality estimation) is enough. Note, that in this case face
                                          structure will lack the member id.
             
             Type: boolean, default: true.

            :optparam estimate_head_pose:  Whether to estimate head pose from the image.
                *Not supported with warped images (see `warped_image` parameter).*
             Type: boolean, default: false.

            :optparam pitch__lt: Pitch threshold. For all the faces with estimated pitch that's more than threshold do not extract descriptor.
               Threshold must be in degrees, in the interval [0,180]. Otherwise, threshold is not taken into account.


             Type: float, maximum: 180, minimum: 0

            :optparam yaw__lt: Yaw threshold. For all the faces with estimated yaw that's more than threshold do not extract descriptor.
               Threshold must be in degrees, in the interval [0,180]. Otherwise, threshold is not taken into account.

             Type: float, maximum: 180, minimum: 0

            :optparam roll__lt: Roll threshold. For all the faces with estimated roll that's more than threshold do not extract descriptor.
              Threshold must be in degrees, in the interval [0,180]. Otherwise, threshold is not taken into account.

             Type: float, maximum: 180, minimum: 0
             
            :optparam extract_exif: Whether to extract EXIF meta information from the input image.
            
             Exact output will vary since there are no mandatory requirements to both authoring software and digital \
             cameras how to write the data.

             This function will only parse the tags and output their names and values as is. Please refer to \
             JEITA CP-3451 EXIF specification for details.
            

            **Example request**:

            :reqheader LUNA-Request-Id: request id

            :reqheader Authorization: basic authorization

            **or**

            :reqheader X-Auth-Token: '16fd2706-8baf-433b-82eb-8c7fada847da'
            
            You must specify Content-Type.
            
            If image is sent:
            
            :reqheader Content-Type: 'image/jpeg', 'image/png', 'image/bmp', 'image/tiff', 'image/gif', 
             'image/x-portable-pixmap'
             
            If descriptor is sent:
            
            :reqheader Content-Type: 'application/x-vl-face-descriptor', 'application/x-vl-xpk'

            For data in base64 is sent:

            :reqheader Content-Type:  'image/x-jpeg-base64', 'application/x-vl-face-descriptor-base64',
             'application/x-vl-xpk-base64',
             'image/x-windows-bmp-base64', 'image/x-png-base64', 'image/x-portable-pixmap-base64',
             'image/x-bmp-base64", 'image/x-tiff-base64', 'image/x-gif-base64'
             
            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 201 Created
                Vary: Accept
                Content-Type: application/json
                LUNA-Request-Id: 1516179740,c06887a2
                
            .. json:object:: extract_result
                :showexample:

                :property faces: faces, which were extracted
                :proptype faces: _list_(:json:object:`extract_one_descriptor`)
                :property  exif: Select image EXIF tags. See CIPA DC-008-2016 for details. Tag to string conversions \
                 are handled by libEXIF.
                :proptype exif: :json:object:`exif`
                
            Error messages are returned in following format :json:object:`server_error`.

            :statuscode 500: internal server error
        """
        qParams = self.fillQueryParams()

        lunaResponse = yield self.lunaCoreContext.aggregateRequestParamAndSendPhotoToLuna(self.request.body,
                                                                                          self.request.headers, qParams)
        for face in lunaResponse['faces']:
            if face.get('attributes') and face['attributes'].get('eyeglasses'):
                face['attributes']['eyeglasses'] = int(bool(face['attributes']['eyeglasses']))

        faces = lunaResponse["faces"]
        if int(qParams["extract_descriptor"]):
            for face in faces:
                photoId = face["id"]
                yield self.luna3Client.lunaFaces.putFace(photoId, attributesId=photoId, accountId=self.accountId,
                                                         raiseError=True)
        self.success(201, outputJson=lunaResponse)

    @StorageHandler.requestExceptionWrap
    @timer
    @gen.coroutine
    def get(self):
        """
        Resource to get all descriptors.
        
        .. http:post:: /storage/descriptors?page=1&page_size=10
        
            :optparam page: A number of page. Minimum 1, default 1. 
            :optparam page_size: Descriptors count on page.  Minimum 1, maximum 100, default 10.
            
            **Example request**:

            :reqheader LUNA-Request-Id: request id

            :reqheader Authorization: basic authorization

            **or**

            :reqheader X-Auth-Token: '16fd2706-8baf-433b-82eb-8c7fada847da'
            
            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 200 Ok
                Vary: Accept
                Content-Type: application/json
                LUNA-Request-Id: 1516179740,c06887a2
                
            :statuscode 200: list of descriptors and number of descriptors are\
             received successfully.
            
            .. json:object:: descriptors_json
                :showexample:

                :property descriptors: descriptor list
                :proptype descriptors: _list_(:json:object:`descriptor`)
                :property count: number of descriptors
                :proptype count: int

            Error messages are returned in following format :json:object:`server_error`.

            :statuscode 500: internal server error
 
        """
        page, pageSize = self.getPagination()

        response = yield self.luna3Client.lunaFaces.getFaces(accountId=self.accountId, pageSize=pageSize,
                                                             page=page,
                                                             raiseError=True)

        self.success(200, outputJson={"descriptors":
                                          [{"id": face["attributes_id"],
                                            "last_update": convertDateTime(face["create_time"]),
                                            "person_id": face["person_id"],
                                            "lists": face["lists"]} for face in response.json["faces"]],
                                      "count": response.json["count"]})

    def setAdditionalDataToAdminStatistic(self, adminStats):
        """
        Set additional stats "count_faces"

        :param adminStats: common stats
        :return: new admin stats
        """
        adminStats.update({"count_faces": str(len(self.statistiData.responseJson["faces"]))})
        return adminStats

    @web.asynchronous
    @timer
    @gen.coroutine
    def on_finish(self):
        """
        Function to send statistics. Called, when account has already received answer.
        """
        if self.request.method == "POST":
            yield self.sendStats()


class GetterPhotoHandler(StorageHandler):

    @StorageHandler.requestExceptionWrap
    @timer
    @gen.coroutine
    def get(self, photo_id, thumbnail):
        """
        Receive descriptor portrait.
        If plug-in is activated, portrait is received by plug-in

        .. http:post:: /storage/portraits/{id}

            :param thumbnail: type of thumbnail
            :param photo_id: descriptor id

            **Example request**:

            :reqheader LUNA-Request-Id: request id

            :reqheader Authorization: basic authorization

            **or**

            :reqheader X-Auth-Token: '16fd2706-8baf-433b-82eb-8c7fada847da'

            **Example response**:

            :reqheader Content-Type: 'image/jpeg'


            Error messages are returned in following format :json:object:`server_error`.

            :statuscode 403: Forbidden, luna-image-store and plug-ins are disabled.
            :statuscode 404: Portrait not found.
            :statuscode 500: Internal server error.
        """
        photo_id = photo_id if thumbnail is None else photo_id + thumbnail
        try:
            for plugin in GETTER_PORTRAITS_PLUGINS:
                res, status = yield plugin(photo_id)
                if status:
                    self.set_header("Content-Type", "image/jpeg")
                    self.write(res)
                    self.set_status(200)
                    return self.finish()
                else:
                    return self.error(404, Error.PortraitNotFound)
        except Exception:
            self.logger.exception()
            return self.error(500, Error.ErrorGetPortraitPlugin)

        if not SEND_TO_LUNA_IMAGE_STORE:
            self.write("Forbidden")
            self.set_header('Content-Type', 'text/html')
            self.set_status(403)
            return self.finish()
        portraitRes = yield self.lunaCoreContext.getPortraitsFromLunaImageStore(photo_id, self.requestId)
        self.success(200, portraitRes, contentType="image/jpeg")
