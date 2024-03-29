<div id="modal-metadata-form-div">
    <form method="POST" id="modal-metadata-form">
        <div class="form-group">

            <label for="modal-metadata-key">Key:</label>
            <input class="form-control form-control-lg" placeholder="key_name (must be single word)"
                id="modal-metadata-key" name="key">

        </div>
        <div class="form-group">

            <label for="modal-metadata-value">Value:</label>
            <input class="form-control form-control-lg" placeholder="key value (any string)" id="modal-metadata-value"
                name="value">

        </div>
        <div class="form-group">
            <button id="modal-metadata-button" type="button" class="btn btn-primary">Add</button>
        </div>
    </form>
</div>

<div id="modal-metadata-listing">
    % if article.metadata_not_autogen.count()>0:
    <table class="table table-striped table-bordered table-hover">
        <tr><td colspan=2>Key</td><td>Value</td></td>
        % for m in article.metadata_not_autogen:
        <tr>
            <td style="width:1%"><button title="Delete this metadata" data-id="{{m.id}}" type="button" class="btn btn-sm btn-danger"
                    onclick="deleteMetadata(this);">&times;</button></td>
            <td> {{m.key}}</td>
            <td>{{m.value}}</td>
        </tr>
        % end
    </table>
    % end
    % if article.metadata_autogen.count()>0:
    <hr />
    <p>These metadata entries are automatically generated from the body of the article.</p>
    <table class="table table-striped table-bordered table-hover">
        % for m in article.metadata_autogen:
        <tr>
            <td>{{m.key}}</td>
            <td>{{m.value}}</td>
        </tr>
        % end
    </table>
    % end
</div>
<script>

    var modal_url = '{{url}}';

    function refreshListing(data) {
        $('#modal-metadata-listing').html(
            $(data).filter('#modal-metadata-listing').html()
        );
    }

    function addMetadata() {
        $.post(
            modal_url, $('#modal-metadata-form').serialize()
        ).done(function (data) {
            refreshListing(data);
        });
    }

    function deleteMetadata(obj) {
        $.post(
            modal_url, { delete: $(obj).data('id') }
        ).done(function (data) {
            refreshListing(data);
        });
    }

    function setEnter(item) {
        item.on("keydown", function (e) {
            if (e.originalEvent.key === "Enter") {
                e.preventDefault();
                $('#modal-metadata-button').click();
            }
        });
    }

    function modalPostLoad() {
        $('#modal-metadata-button').on('click', function () {
            addMetadata();
        });
        setEnter($("#modal-metadata-value"));
        setEnter($("#modal-metadata-key"));
    }

    function modalPostEnter() {}

</script>