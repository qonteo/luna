var minSimilarity = 0.6;
var showSimilarity = true;
var minPassportSimilarity = 0.4;
var showPassportIcon = true;
var blocks_count = 0;
var showAttributes = true;
var stack = [];
$(document).ready(function () {
    var temp;
    temp = localStorage.getItem('minSimilarity');
    if (temp != undefined) {
        minSimilarity = temp;
        $('.minSimilarity_value').val(minSimilarity);
    }

    temp = localStorage.getItem('showSimilarity');
    showSimilarity = (temp == "true") ? true : false;
    $('#view_similarity').prop('checked', showSimilarity);

    temp = localStorage.getItem('showConnectID');
    if (temp == "false") {
        document.getElementById('connectID_logo').style.display = "none";
    }
    $('#view_connectID_logo').prop('checked', ((temp == 'true') ? true : false));


    temp = localStorage.getItem('minPassportSimilarity');
    if (temp != undefined) {
        minPassportSimilarity = temp;
        $('.minPassportSimilarity_value').val(minPassportSimilarity);
    }

    temp = localStorage.getItem('showPassportIcon');
    if (temp == "false") {
        var temp_element = document.getElementById('passport_icon');
        if (temp_element) {
            temp_element.style.display = "none";
        }
    }

    showAttributes = !!localStorage.getItem('viewAttributes')
    $('#view_attributes').prop('checked', showAttributes)

    $('#view_passport_icon').prop('checked', ((temp == 'true') ? true : false));

});

function initSockets(namespace, troom) {
    $(document).ready(function () {



        $('.minSimilarity_value').val(minSimilarity);
        $('.minPassportSimilarity_value').val(minPassportSimilarity);
        $('.open_minSimilarity_correct')
            .on('click', function () {
                $('.minSimilarity_correct').addClass('active');
            });
        $('.minSimilarity_correct .save')
            .on('click', function () {
                minSimilarity = $('.minSimilarity_value').val().trim();
                localStorage.setItem('minSimilarity', minSimilarity);
                showSimilarity = $('#view_similarity').prop('checked');
                localStorage.setItem('showSimilarity', showSimilarity);

                showAttributes = $('#view_attributes').prop('checked')
                localStorage.setItem('viewAttributes', showAttributes)

                minPassportSimilarity = $('.minPassportSimilarity_value').val().trim();
                localStorage.setItem('minPassportSimilarity', minPassportSimilarity);
                showPassportIcon = $('#view_passport_icon').prop('checked');
                localStorage.setItem('showPassportIcon', showPassportIcon);

                var show_connectID = $('#view_connectID_logo').prop('checked');
                if (show_connectID) {
                    document.getElementById('connectID_logo').style.display = "inherit";
                } else {
                    document.getElementById('connectID_logo').style.display = "none";
                }
                localStorage.setItem('showConnectID', show_connectID);
                $('.minSimilarity_correct').removeClass('active');
                alert('Similarity:  ' + minSimilarity + ' (' + (minSimilarity * 100) + '%)\n Passport_Similarity:  ' + minPassportSimilarity + ' (' + (minPassportSimilarity * 100) + '%) \n view_Similarity:  ' + showSimilarity + ' \n view_connectID_logo:  ' + show_connectID + ' \n view_Passport_Icon:  ' + showPassportIcon + ' \n view_attributes: ' + showAttributes);
            });






        var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);
        var timeout_id;
        socket.on('event', function (msg) {
            var eventT = msg.data;
            if (troom == 'mobile_room') {
                var $_container = $('.recognition-block');
                var $_text = $('.recognition-block__text');
            } else if (troom == 'passport_room') {
                var $_container = $('.passport-stream__wrap');
            } else {
                var $_container = $('.video-stream__wrap');
            }
            if (msg.data['data'] != 'wait') {
                if (msg.data && msg.data['data'] && msg.data['data']['candidates'] && msg.data['data']['candidates'][0] && (msg.data['data']['candidates'][0]['similarity'] > minSimilarity || troom == 'passport_room')) {

                    var candidate = msg.data['data']['candidates'][0];
                    var reference = msg.data['data']['face'];

                    if (troom == 'mobile_room') {
                        clearTimeout(timeout_id);
                        $_container.removeClass('recognition-block--denied');
                        $_container.addClass('recognition-block--granted');
                        $_text.text(candidate['user_data'] + ', Access Granted');

                    } else if (troom == 'passport_room') {
                        clearTimeout(timeout_id);
                        var params = '';
                        var params_array = JSON.parse(msg.data['data']['passport_data']['identification']);
                        //---------------------------------------------
                        var surname_data = '';
                        var name_data = '';
                        var patronymic_data = '';


                        //----------------------------------
                        for (var key in params_array) {
                            var tmp = '<p>' + key + ': ' + params_array[key] + '</p>';
                            if (key.indexOf("surname") == 0) {
                                surname_data = tmp;
                            } else if (key.indexOf("name") == 0) {
                                name_data = tmp;
                            } else if (key.indexOf("patronymic") == 0) {
                                patronymic_data = tmp;
                            } else {
                                params += tmp;
                            }
                        }
                        params = surname_data + name_data + patronymic_data + params;
                        //----------------------------------
                        var passport_block = '<div class="passport-stream__block-left">' +
                            '<img src="data:image/jpeg;base64,' + msg.data['data']['passport_photo'] + '" alt="" class="passport-stream__block-left_img">' +
                            '<div class="passport-stream__block-left_content">' +
                            '<h5 class="video-stream__block-content-title">Document info:</h5>' +
                            params +
                            '</div>' +
                            '</div>' +
                            '<div class="passport-stream__block-right">' +
                            '<h5 class="video-stream__block-content-title">' + ((candidate['similarity'] < minPassportSimilarity) ? 'No matches found' : candidate['user_data']) + '</h5>' +
                            ((candidate['similarity'] < minPassportSimilarity) ? '' : '<img src="/luna/storage/portraits/' + candidate['descriptor_id'] + '" alt="" class="passport-stream__block-right_img">') +
                            '</div>';

                        $_container.addClass('hide');
                        setTimeout(function () {
                            $_container.removeClass('hide');
                            $_container.html(passport_block);
                            $_container.addClass('view');
                            setTimeout(function () {
                                $_container.removeClass('view');
                            }, 100);
                        }, 1500);

                        // setTimeout(function () {
                        //     $_block.removeClass('new');
                        // }, 100);

                    } else {
                        var now = new Date();
                        var months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
                        var date = now.getHours() + ':' + ((now.getMinutes() < 10) ? '0' : '') + now.getMinutes() + ', ' + now.getDate() + ' ' + months[now.getMonth()];
                        var stream_block = '<div class="video-stream__block new">' +
                            '<div class="video-stream__block-img-wrap">' +
                            '<img src="/luna/storage/portraits/' + reference['id'] + '" alt="" class="video-stream__block-img">' +
                            '</div>' +
                            '<div class="video-stream__block-content">' +
                            '<h5 class="video-stream__block-content-title">' + candidate['user_data'] + '</h5>' +
                            '<table class="video-stream__block-content-table">' +

                            '<tr class="video-stream__block-content-table-row">' +
                            '<td class="video-stream__block-content-table-col">' + ((showSimilarity) ? '<span class="video-stream__block-content-table-text video-stream__block-content-table-text--transparent"> Similarity </span>' : '') + '</td>' +
                            '<td class="video-stream__block-content-table-col">' + ((showSimilarity) ? '<span class="video-stream__block-content-table-text">' + ((candidate['similarity'] * 100).toFixed(2)) + '%</span>' : '') + '</td>' +
                            '</tr>' +

                            '<tr class="video-stream__block-content-table-row">' +
                            '<td class="video-stream__block-content-table-col">' +
                            '<span class="video-stream__block-content-table-text video-stream__block-content-table-text--transparent"> ID </span>' +
                            '</td>' +
                            '<td class="video-stream__block-content-table-col">' +
                            '<span class="video-stream__block-content-table-text">' + candidate['person_id'] + '</span>' +
                            '</td>' +
                            '</tr>' +

                            '<tr class="video-stream__block-content-table-row">' +
                            '<td class="video-stream__block-content-table-col">' +
                            '<span class="video-stream__block-content-table-text video-stream__block-content-table-text--transparent"> Time </span>' +
                            '</td>' +
                            '<td class="video-stream__block-content-table-col">' +
                            '<span class="video-stream__block-content-table-text">' + date + '</span>' +
                            '</td>' +
                            '</tr>' +
                            (!showAttributes ? '' : (
                            '<tr class="video-stream__block-content-table-row">' +
                            '<td class="video-stream__block-content-table-col">' +
                            '<span class="video-stream__block-content-table-text video-stream__block-content-table-text--transparent"> Age </span>' +
                            '</td>' +
                            '<td class="video-stream__block-content-table-col">' +
                            '<span class="video-stream__block-content-table-text">' + Number((reference['attributes']['age']).toFixed(0)) + '</span>' +
                            '</td>' +
                            '</tr>' +

                            '<tr class="video-stream__block-content-table-row">' +
                            '<td class="video-stream__block-content-table-col">' +
                            '<span class="video-stream__block-content-table-text video-stream__block-content-table-text--transparent"> Gender </span>' +
                            '</td>' +
                            '<td class="video-stream__block-content-table-col">' +
                            '<span class="video-stream__block-content-table-text">' + (reference['attributes']['gender'] >= 0.5 ? 'Male' : 'Female') + '</span>' +
                            '</td>' +
                            '</tr>')) +

                            // '<tr class="video-stream__block-content-table-row">' +
                            // '<td class="video-stream__block-content-table-col">' +
                            // '<span class="video-stream__block-content-table-text video-stream__block-content-table-text--transparent"> Glasses </span>' +
                            // '</td>' +
                            // '<td class="video-stream__block-content-table-col">' +
                            // '<span class="video-stream__block-content-table-text">' + Number(reference['attributes']['eyeglasses']).toFixed(2) + '</span>' +
                            // '</td>' +
                            // '</tr>' +

                            '</table>' +
                            '</div>' +
                            '</div>';
                        $_container.prepend(stream_block);
                        var $_block = $('.video-stream__block.new');

                        setTimeout(function () {
                            $_block.removeClass('new');
                        }, 100);
                        blocks_count++;
                        if (blocks_count >= 50) {
                            blocks_count--;
                            // $_container.remove(":last-child");
                            $(".video-stream__wrap .video-stream__block:nth-last-child(1)").remove();
                        }
                    }
                } else {
                    if (troom == 'mobile_room') {
                        clearTimeout(timeout_id);
                        $_container.removeClass('recognition-block--granted');
                        $_container.addClass('recognition-block--denied');
                        $_text.text('Access Denied');
                    }
                }

                if (troom == 'mobile_room') {
                    timeout_id = setTimeout(function () {
                        $_container.removeClass('recognition-block--denied');
                        $_container.removeClass('recognition-block--granted');
                        $_text.text('Please use a mobile phone to continue');
                    }, 10000);
                }
                // if(troom == 'passport_room') {
                //     timeout_id = setTimeout(function () {
                //         $_container.removeClass('recognition-block--denied');
                //         $_container.removeClass('recognition-block--granted');
                //         $_container.html('<span class="waiting">Waiting</span>');
                //     }, 60000);
                // }
            }
            console.log('->');
            console.log(eventT);
        });
        socket.on('connect', function () {
            socket.emit('join', { room: troom });
        });

    });
}



function initWebPhotoMaker() {
    $(document).ready(function () {

        var minSimilarity = 0.6;

        function resetSettings() {
            photoMaker.setMovementThreshold(0.2);
            photoMaker.setBestShotScoreThreshold(0.08);
            photoMaker.setRotationThreshold(50);
            photoMaker.setMinFaceScaleFactor(0.15);
            photoMaker.setMaxNumberOfFramesWithoutDetection(8);
        }

        var trackIds = [-1, -1, -1, -1, -1, -1];
        var trackNames = ["", "", "", "", "", ""];

        //--------------------------------------------------------------------------
        // Globals.
        var meter = new FPSMeter(document.getElementById('video-container'), { graph: 1 });
        // Video input & output canvas.
        var video = document.getElementById('webcam');
        var overlay = document.getElementById('overlay');
        var overlayCC = overlay.getContext('2d');
        var bestShot = document.getElementById('best-shot');
        var bestShotCC = bestShot.getContext('2d');
        var buffer = document.createElement("canvas");
        var bufferCC = buffer.getContext('2d');

        // Web camera video stream.
        var localMediaStream = null;

        // Frame buffer parameters.
        var width;
        var height;
        var nativeFrameBuffer;
        var nativeFrameBufferData;

        var returnPortraitWidth;
        var returnPortraitHeight;
        var returnPortraitWidthData;
        var returnPortraitHeightData;

        var nativeBestShotBuffer;
        var nativeBestShotBufferData;
        var bestShotImageData;

        var detectionSmoothing = 0.9999999;

        var photoMaker = null;
        var smoother = null;

        var alreadyHaveBestShot = false;
        var alreadyHaveFinalShot = false;
        //--------------------------------------------------------------------------
        // Functions.

        // Reset tracker & clear the best shot.
        function reset() {
            photoMaker.reset();
            bestShotCC.clearRect(0, 0,
                bestShot.width,
                bestShot.height);

            alreadyHaveBestShot = false;
            alreadyHaveFinalShot = false;

            document.getElementById("exp-mov").innerHTML = "";
        }

        function getName(trackId) {
            var count = -1;
            for (var j = 0; j < trackIds.length; j++) {
                if (trackIds[j] == trackId) {
                    count = j;
                    break;
                }
            }
            if (count == -1)
                return "";
            else
                return trackNames[count]

        }

        // Draw current detection rectangle.
        function visualizeDetection(ctx, xywh, radius, color, trackId) {
            radius = 1;
            ctx.save();
            ctx.strokeStyle = "rgba("
                + color[0] + ", "
                + color[1] + ", "
                + color[2] + ", "
                + color[3] + ")";


            ctx.lineWidth = 4;

            try {
                var sx = xywh.x;
                var sy = xywh.y;
                var ex = xywh.x + xywh.width;
                var ey = xywh.y + xywh.height;
                var r = radius;

                var r2d = Math.PI / 180;

                if ((ex - sx) - (2 * r) < 0) {
                    r = ((ex - sx) / 2);
                } //ensure that the radius isn't too large for x
                if ((ey - sy) - (2 * r) < 0) {
                    r = ((ey - sy) / 2);
                } //ensure that the radius isn't too large for y



                ctx.beginPath();
                ctx.moveTo(sx + r, sy);
                ctx.lineTo(ex - r, sy);
                ctx.arc(ex - r, sy + r, r, r2d * 270, r2d * 360, false);
                ctx.lineTo(ex, ey - r);
                ctx.arc(ex - r, ey - r, r, r2d * 0, r2d * 90, false);
                ctx.lineTo(sx + r, ey);
                ctx.arc(sx + r, ey - r, r, r2d * 90, r2d * 180, false);
                ctx.lineTo(sx, sy + r);
                ctx.arc(sx + r, sy + r, r, r2d * 180, r2d * 270, false);
                ctx.closePath();
                ctx.font = "30pt Calibri";
                ctx.fillStyle = "#00ff00";
                // ctx.fillStyle = "#783674";
                ctx.direction = "rtl";
                // ctx.textAlign  = "right";
                // Направление текста. Возможные значения: ltr, rtl, inherit. По умолчанию равно inherit.
                var name = getName(trackId);
                ctx.fillText(name, sx, sy - 5);
                ctx.stroke();
                ctx.restore();
            } catch (err) {
                console.log("BAD VALUE OF DETECTION");
                // ��������� ������

            }
        }

        function getSize(array4) {
            var res = 0;
            var pow2 = 1;
            for (var i = 0; i < array4.length; i++) {
                res += array4[i] * pow2;
                pow2 *= 256;
            }
            return res;
        }


        function fellIds(ids) {
            for (var j = 0; j < trackIds.length; j++) {
                var countBad = 0;
                for (var i = 0; i < ids.length; i++) {
                    if (ids[i] != trackIds[j])
                        countBad++;
                    else
                        break;
                }
                if (countBad == ids.length) {
                    trackIds[j] = -1;
                    trackNames[j] = "";
                }
            }

            for (var i = 0; i < ids.length; i++) {
                var newTrack = true;
                for (var j = 0; j < trackIds.length; j++) {
                    if (ids[i] == trackIds[j]) {
                        newTrack = false
                        break;
                    }
                }
                if (newTrack) {
                    for (var j = 0; j < trackIds.length; j++) {
                        if (trackIds[j] == -1) {
                            trackIds[j] = ids[i];
                            break;
                        }
                    }
                }
            }
        }

        var sendedIds = [];

        function checkIdNotTracked(trackId) {
            var idx = trackIds.indexOf(trackId);
            var nameExist = trackNames[idx] !== "";
            return (sendedIds.indexOf(trackId) < 0) && !nameExist;
        }

        function removeIdFromSended(trackId) {
            var idx = sendedIds.indexOf(trackId);
            sendedIds.splice(idx, 1);
            console.log(trackId, " removed from ", sendedIds)
        }

        function sendToFaceIs(trackId) {
            console.log("ajax start")
            var dataURL = bestShot.toDataURL("image/jpeg");
            dataURLclean = dataURL.replace(/^data:image\/(jpeg);base64,/, "");
            // send image to cloud service for processing and recognition

            var findedData = [];

            function processFindedData() {
                var newArray = findedData.map(function(el){
                    return el.candidates;
                });
                findedData = [];

                var flattened = newArray.reduce(function (array, value) {
                    return array.concat(value);
                }, []);

                $.each(flattened, function (i, v) {

                    console.log("########### Success ajax data: " + v.similarity + " Name: " + v.user_data);

                    if (v.similarity > minSimilarity) {
                        for (var j = 0; j < trackIds.length; j++) {
                            if (trackIds[j] == trackId) {
                                trackNames[j] = v.user_data;
                                break;
                            }
                        }
                    }
                    else {
                        photoMaker.discardBestShot(trackId);
                        testName = "";
                    }

                }); // $.each
            }

            sendedIds.push(trackId);

            LISTS_FOR_ID.slice(0,1).forEach(function (list) {
                $.ajax({
                    // url: 'https://visionlabs.faceis.ru/client/search',
                    url: '/luna/matching/search?list_id=' + list,
                    contentType: 'image/x-jpeg-base64',
                    dataType: 'json',
                    data: dataURLclean,
                    type: 'POST',

                    success: function (faceISdata) {
                        findedData.push(faceISdata);
                        //photoMaker.reset();
                        console.log("########### Success ajax!");
                        //blocReqestToFaceIs = false;
                        if (findedData.length === LISTS_FOR_ID.length - 1) {
                            removeIdFromSended(trackId);
                            processFindedData();
                        }
                    }, // success
                    error: function (jqXhr, textStatus, errorThrown) {
                        removeIdFromSended(trackId);
                        console.log("############ Error ajax: " + errorThrown);
                        if (findedData.length > 0) {
                            removeIdFromSended(trackId);
                            processFindedData();
                        }
                    }
                });
            });
        }

        // Process one frame.
        function process() {
            meter.tickStart();
            // download video frame data to a canvas buffer
            bufferCC.drawImage(video, 0, 0, width, height);

            // take the buffer contents
            var bufferImageData = bufferCC.getImageData(0, 0, width, height);

            // convert image data to typed byte array (raw bytes)
            nativeFrameBufferData.set(bufferImageData.data, 0);


            // process raw bytes
            photoMaker.submitRawImage(nativeFrameBuffer, width, height);
            photoMaker.update();
            overlayCC.clearRect(0, 0, overlay.width, overlay.height);
            var strIds = photoMaker.getIds();
            var jIds = JSON.parse(strIds);
            var ids = jIds["ids"];
            fellIds(ids);
            if (ids.length)//photoMaker.haveFaceDetection())
            {
                for (var i = 0; i < ids.length; i++) {
                    var id = ids[i];
                    var detection = photoMaker.getSmoothedFaceDetection(id);


                    var predicted = photoMaker.faceDetectionIsPredicted(id);

                    var color = [0, 255, 0, 255];

                    var verdict = "";
                    var speedSlow = photoMaker.isSlowMovement(id);
                    if (!speedSlow) verdict = "TOO FAST!!!";
                    if (predicted) verdict = "PREDICT";

                    if (predicted || !speedSlow) {

                        color = [255, 0, 0, 255];
                    }
                    visualizeDetection(overlayCC, detection, 10, color, id);

                    if (photoMaker.getCurrentFrameNumber() == photoMaker.getBestShotFrameNumber(id)) {
                        alreadyHaveFinalShot = true;

                        photoMaker.getBestShotRaw(id, nativeBestShotBuffer, returnPortraitWidth, returnPortraitHeight);
                        var portraitWidth = getSize(returnPortraitWidthData);
                        var portraitHeight = getSize(returnPortraitHeightData);
                        if (portraitWidth > 0) {
                            var tempImageData = bestShotCC.createImageData(portraitWidth, portraitHeight);

                            for (var i = 0; i < portraitHeight; i++) {
                                for (var j = 0; j < portraitWidth; j++) {
                                    for (var k = 0; k < 4; k++) {
                                        tempImageData.data[i * 4 * portraitWidth + j * 4 + k] = nativeBestShotBufferData[i * 4 * portraitWidth + j * 4 + k];
                                    }
                                }
                            }
                            bestShot.width = portraitWidth;
                            bestShot.height = portraitHeight;
                            bestShotCC.putImageData(tempImageData, 0, 0);
                            //addPhoto(id);
                            if (checkIdNotTracked(id)) {
                                sendToFaceIs(id);
                            }
                        }
                    }
                }
            }
            else {
                smoother = null;
            }

            // update the best shot if it has changed

            //current shot is best
            meter.tick();
        }//process

        // `Process` wrapped in a timer.
        function processProfiled() {
            var start = new Date();
            {
                process();
            }
            var end = new Date();

            console.log("process took " + (end.getTime() - start.getTime()) + " ms");
        }

        // Camera capture.
        function capture() {
            if (localMediaStream)
                process();

            requestAnimationFrame(capture);
        }

        // PhotoMaker module initialization.
        function initialize(frameWidth, frameHeight) {
            width = frameWidth;
            height = frameHeight;

            // resize internla buffers accordingly
            buffer.width = width;
            buffer.height = height;
            overlay.width = width;
            overlay.height = height;


            // compute staging memory requirements
            var bufferSize = width * height * 4;

            // allocate staging memory
            nativeFrameBuffer = Module._malloc(bufferSize);
            nativeFrameBufferData = new Uint8ClampedArray(
                Module.HEAPU8.buffer,
                nativeFrameBuffer, bufferSize);


            returnPortraitWidth = Module._malloc(4);
            returnPortraitHeight = Module._malloc(4);

            returnPortraitWidthData = new Uint8ClampedArray(
                Module.HEAPU8.buffer,
                returnPortraitWidth, 4);
            returnPortraitHeightData = new Uint8ClampedArray(
                Module.HEAPU8.buffer,
                returnPortraitHeight, 4);


            bufferSize = width * height * 4;//bestShot.width * bestShot.height * 4;

            nativeBestShotBuffer = Module._malloc(bufferSize);
            nativeBestShotBufferData = new Uint8ClampedArray(
                Module.HEAPU8.buffer,
                nativeBestShotBuffer, bufferSize);


            photoMaker = new Module.WebPhotoMakerM();
            resetSettings();
        }


        //--------------------------------------------------------------------------
        // Initialization.

        Module.onRuntimeInitialized = function () {

            // Video constraints.
            var constraints = {
                video: {
                    mandatory: {
                        maxWidth: 640,
                        maxHeight: 480
                    }
                }
            };

            function successCallback(stream) {
                // Set the source of the video element with the stream from the camera
                if (video.mozSrcObject !== undefined) {
                    video.mozSrcObject = stream;
                } else {
                    video.src = (window.URL && window.URL.createObjectURL(stream)) || stream;
                }

                localMediaStream = stream;

                video.onloadedmetadata = function () {
                    initialize(
                        video.videoWidth,
                        video.videoHeight);
                    capture();
                };

                video.play();
            }

            function errorCallback(error) {
                console.error('An error occurred: [CODE ' + error.code + ']');
            }

            navigator.getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia || navigator.msGetUserMedia;
            window.URL = window.URL || window.webkitURL || window.mozURL || window.msURL;

            // Call the getUserMedia method with our callback functions
            if (navigator.getUserMedia) {
                navigator.getUserMedia(constraints, successCallback, errorCallback);
            } else {
                console.log('Native web camera streaming (getUserMedia) not supported in this browser.');
            }
        };
    });
}
