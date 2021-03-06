<form method="POST" id="modal-search-form">
    <div id="wiki-modal-search" class="form-group">
        <label for="modal-search-query">Type to search:</label>
        <input class="form-control form-control-lg" placeholder="Name or description" id="modal-search-query"
            name="search_query">
    </div>
    % if "alt_input" in locals():
    <div class="form-group">
        <input class="form-control form-control-lg" placeholder="{{alt_input[0]}}" id="modal-alt-input" name="{{alt_input[1]}}">
    </div>
    % end
    <div id="modal-search-results">{{!search_results}}</div>
</form>
<script>

    var modal_url = '{{url}}';

    $("#modal-search-query").on("keyup", function () {
        searchForm = $('#modal-search-form').serialize();
        $.post(
            modal_url,
            searchForm
        ).done(function (data) {
            $("#modal-search-results").html(data);
        });
    });

    // send events on alt input box to main input box

    $("#modal-alt-input").on("keydown", function (e) {
        if (e.originalEvent.key === "Enter") {
            e.preventDefault();
            $("#modal-search-query").trigger(e);
        }
    });  
    
    function modalPostLoad() {
        searchbox = $("#modal-search-query")
        searchbox.focus();
        setEnterEvent(searchbox);
    }
</script>