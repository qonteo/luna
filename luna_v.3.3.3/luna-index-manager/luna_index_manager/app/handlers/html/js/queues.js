
  var pageNumberQueue = 1;
  var pageSizeQueue = 10;
  var queueURL = "/1/queue?page="+pageNumberQueue+'&page_size='+pageSizeQueue;

  function getQueueURL() {
    queueURL = "/1/queue?page="+pageNumberQueue+'&page_size='+pageSizeQueue;
    return queueURL;
  };

  function convertDateTimeToHumanReadableFormat (inputDateTime, type, row) {
    if (inputDateTime === null) {return '';}
    if (moment(inputDateTime).isValid()) {
      return moment(inputDateTime).format('YYYY-MM-DD<br>HH:mm');
    }
    else{
      return 'DateTime format error. Required format ISO8601';
    }
  };

  function updateQueueTable(inputTable){
    if (pageNumberQueue < 1){
      pageNumberQueue = 1;
    }
    document.getElementById('curQueuePage').value = pageNumberQueue.toString();
    inputTable.page.len(pageSizeQueue);
    inputTable.ajax.url(getQueueURL()).load();

  };

  $(document).ready(function() {
      var queuesTable = $('#tableQueues').DataTable( {
          ajax: {
            url:getQueueURL(),
            dataSrc: 'lists',
            type: 'GET',
          },
          dom: '<"top"B><"toolbar">t',
          ordering: false,
          lengthChange: true,
          //scrollY: parseInt($(document).height()*0.35)+"px",
          //scrollCollapse: true,
          columns: [
              { data: "list_id" },
              { data: "last_update_time" },
              { data: "face_count" },
          ],
          buttons:[
            {text: '<', action(e, dt, node, config) {
              pageNumberQueue = pageNumberQueue - 1;
              updateQueueTable(queuesTable);
            }},
            {text: '>', action(e, dt, node, config) {
              pageNumberQueue = pageNumberQueue + 1;
              updateQueueTable(queuesTable);
            }},
            {text: 'show 10', action(e, dt, node, config) {
              pageSizeQueue = 10;
              updateQueueTable(queuesTable);
            }},
            {text: 'show 50', action(e, dt, node, config) {
              pageSizeQueue = 50;
              updateQueueTable(queuesTable);
            }},
            {text: 'show 100', action(e, dt, node, config) {
              pageSizeQueue = 100;
              updateQueueTable(queuesTable);
            }},
          ],

      } );

      $("div.toolbar", queuesTable.table().container()).html('' +
        'CurrentPage: <input style="height:33px;width:75px" type="text" id="curQueuePage" value="1">' +
        '<button style="margin-left:200px;" id="patchClear" onclick="patchClear()">Clear</button>');

      $('#curQueuePage').on('change', function(){
        pageNumberQueue = this.value;
        updateQueueTable(queuesTable);
      });
  } );