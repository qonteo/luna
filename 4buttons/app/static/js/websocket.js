function init_ws (location,port) {
    console.log(location.port);
    if (location.port == undefined || location.port != 80) {
        websocket_conn = "ws://{}:{}/ws".format(location, port);
    } else {
        websocket_conn = "ws://{}/ws".format(location);
    }

    conn = new WebSocket(websocket_conn);

    conn.onopen = function (e) {
        console.log('Success connect to {}'.format(websocket_conn));
    };
    conn.onmessage = function (e) {
        event = JSON.parse(e.data)['event'];
        addFacestreamDataTable(JSON.parse(event));
    };

    conn.onclose = function (e) {
        console.log('Connection closed')
        setTimeout(function(){init_ws_connection(location,port);}, 2000);
    };

};



function sendMessage(msg) {
        waitForSocketConnection(conn, function() {
            conn.send(msg);
        });
    };


function waitForSocketConnection(socket, callback){
        setTimeout(
            function(){
                if (socket.readyState === 1) {
                    if(callback !== undefined){
                        callback();
                    }
                    return;
                } else {
                    waitForSocketConnection(socket,callback);
                }
            }, 100);
};


function init_ws_connection(location,port) {
    websocket = init_ws(location,port);
    // last part of URI is id of source
    association_message = {"command":"associate","source_id":window.location.href.split("/").pop()}
    sendMessage(JSON.stringify(association_message));
}

