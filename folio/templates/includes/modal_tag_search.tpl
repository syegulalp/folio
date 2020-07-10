% include('includes/modal_search_core.tpl')

<script>

    function modalPostEnter() {
        if ($("#modal-search-query").val().length) {
            $.post(
                articleTarget + "/add-tag",
                { tag: $("#modal-search-query").val() }
            ).done(function (data) {
                $("#modal-search-query").val('');
                $('#modal-tag-listing').html(data);
            })
        }
    }

</script>