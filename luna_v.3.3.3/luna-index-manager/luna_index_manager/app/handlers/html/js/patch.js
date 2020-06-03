
function patchForward(){
  var listId = document.getElementById('patchListId').value;
    $.ajax({
    url: '/1/queue?list_id='+listId+'&action=forward',
    dataType: "json",
    type: 'PATCH',
    success: function (data, textStatus, xhr) {
      if (parseInt(xhr.status) != 204) {
        document.getElementById('patchResult').innerHTML = "Patch (forward) failed";
      }
      else{
        document.getElementById('patchResult').innerHTML = "Patch (forward) success";
      }
    },
    error: function (data) {
      document.getElementById('patchResult').innerHTML = "Patch (forward) failed";
    }
  });
};

function patchClear(){
    $.ajax({
    url: '/1/queue?action=clear',
    dataType: "json",
    type: 'PATCH',
    success: function (data, textStatus, xhr) {
      if (parseInt(xhr.status) != 204) {
        document.getElementById('patchResult').innerHTML = "Patch (clear) failed";
      }
      else{
        document.getElementById('patchResult').innerHTML = "Patch (clear) success";
      }
    },
    error: function (data) {
      document.getElementById('patchResult').innerHTML = "Patch (clear) failed";
    }
  });
};