
  var indexesListsURL = "/1/indexes/lists";

  $(document).ready(function() {
      var indexesListsTable = $('#tableIndexesLists').DataTable( {
          ajax: {
            url:indexesListsURL,
            type: 'GET',
            dataSrc: 'lists',
          },
          dom: 'lrtip',
          pagingType: "full_numbers",
          ordering: false,
          lengthChange: true,
          columns: [
              { data: "list_id" },
              { data: "generation" },
          ],

      } );

      indexesListsTable.ajax.url(indexesListsURL).load();

  } );