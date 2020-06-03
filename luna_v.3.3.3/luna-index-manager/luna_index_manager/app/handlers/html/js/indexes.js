
  var pageNumberIndexes = 1;
  var pageSizeIndexes = 10;
  var queryStatus = null;
  var queryListIds = null;
  var queryGenerations = null;
  var indexesURL = "/1/indexes?&page="+pageNumberIndexes+'&page_size='+pageSizeIndexes;

  function getIndexesURL() {
    indexesURL = "/1/indexes?&page="+pageNumberIndexes+'&page_size='+pageSizeIndexes;
    if (queryStatus != null && queryStatus.toString() != '' && queryStatus.toString() != 'NaN'){
      indexesURL += '&status='+queryStatus.toString();
    }
    if (queryListIds != null && queryListIds.toString() != ''){
      indexesURL += '&list_ids='+queryListIds;
    }
    if (queryGenerations != null && queryGenerations.toString() != ''){
      indexesURL += '&generations='+queryGenerations;
    }
    return indexesURL;
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

  function updateIndexesTable(inputTable){
    if (pageNumberIndexes < 1){
      pageNumberIndexes = 1;
    }
    document.getElementById('curIndexesPage').value = pageNumberIndexes.toString();
    inputTable.page.len(pageSizeIndexes);
    inputTable.ajax.url(getIndexesURL()).load();
  };

  $(document).ready(function() {
      var indexesTable = $('#tableIndexes').DataTable( {
          ajax: {
            url:getIndexesURL(),
            dataSrc: 'tasks',
            type: 'GET',
          },
          dom: '<"top"B><"toolbar">t',
          ordering: false,
          lengthChange: true,
          //scrollY: parseInt($(document).height()*0.35)+"px",
          //scrollCollapse: true,
          columns: [
              { data: "task_id" },
              { data: "generation" },
              { data: "list_id" },
              { data: "status" },
              { data: "start_index_time", render: convertDateTimeToHumanReadableFormat},
              { data: "end_index_time", render: convertDateTimeToHumanReadableFormat },
              { data: "start_upload_index_time", render: convertDateTimeToHumanReadableFormat },
              { data: "end_upload_index_time", render: convertDateTimeToHumanReadableFormat },
              { data: "start_reload_index_time", render: convertDateTimeToHumanReadableFormat },
              { data: "end_reload_index_time", render: convertDateTimeToHumanReadableFormat },
              { data: "start_time", render: convertDateTimeToHumanReadableFormat },
              { data: "end_time", render: convertDateTimeToHumanReadableFormat },
              { data: "last_update_time", render: convertDateTimeToHumanReadableFormat },
              { defaultContent: '<button>Show error</button>', data: null}
          ],
          buttons:[
            {text: '<', action(e, dt, node, config) {
              pageNumberIndexes = pageNumberIndexes - 1;
              updateIndexesTable(indexesTable);
            }},
            {text: '>', action(e, dt, node, config) {
              pageNumberIndexes = pageNumberIndexes + 1;
              updateIndexesTable(indexesTable);
            }},
            {text: 'show 10', action(e, dt, node, config) {
              pageSizeIndexes = 10;
              updateIndexesTable(indexesTable);
            }},
            {text: 'show 50', action(e, dt, node, config) {
              pageSizeIndexes = 50;
              updateIndexesTable(indexesTable);
            }},
            {text: 'show 100', action(e, dt, node, config) {
              pageSizeIndexes = 100;
              updateIndexesTable(indexesTable);
            }},
          ],

      } );

      $("div.toolbar", indexesTable.table().container()).html('' +
        'CurrentPage: <input style="height:33px;width:75px" type="text" id="curIndexesPage" value="1">' +
        '   ' +
        '<input style="margin-left:200px;width:150px;" type="text" id="queryListIds" placeholder="list ids (UUIDs) [1,2]">' +
        '<input style="width:150px" type="text" id="queryGenerations" placeholder="generations [1,2]">' +
        '      <select id="indexStatus">\n' +
        '        <option value="">Status: All</option>\n' +
        '        <option value="0">Status: Success (0)</option>\n' +
        '        <option value="1">Status: Fail (1)</option>\n' +
        '      </select>\n'
      );

      $('#curIndexesPage').on('change', function(){
        pageNumberIndexes = this.value;
        updateIndexesTable(indexesTable);
      });

      $('#indexStatus').on('change', function(){
        queryStatus = parseInt(this.value);
        updateIndexesTable(indexesTable);
      });

      $('#queryListIds').on('change', function () {
        queryListIds = this.value;
        updateIndexesTable(indexesTable);
      });

      $('#queryGenerations').on('change', function () {
        queryGenerations = this.value;
        updateIndexesTable(indexesTable);
      });

      $('#tableIndexes tbody').on('click', 'button', function () {
        var data = indexesTable.row( $(this).parents('tr') ).data();
        if (data['error'] != null){
          alert("\""+data['error']['error_message']+"\""+' at '+data['error']['error_time']);
        }
        else{
          alert('No error');
        }
      });

  } );