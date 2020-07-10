% include('includes/modal_search_core.tpl')

<script>

    function modalPostEnter() {
        insertLink(
            $("#modal-search-query").val(),
            $("#modal-alt-input").val()
        );
    }

    function modalPostShiftEnter() {
        insertLink(
            $("#modal-search-query").val(),
            $("#modal-alt-input").val()
        );
    }

</script>