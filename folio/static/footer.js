var drop_timeout;

function reset_msg() {
    clearTimeout(drop_timeout);
    d = $("#drop-message")
    d.stop().animate({ opacity: '100' });
    d.hide();
}

function is_file(e) {
    return e.originalEvent.dataTransfer.types[0] == "Files";
}

$(document).on('dragover', function (e) {
    if (is_file(e)) {
        e.preventDefault();
    }
});

$(document).on('drop', function (e) {
    if (is_file(e)) {
        e.preventDefault();
    }
});

$(document).on('dragenter', function (e) {
    if (is_file(e)) {
        $("#drop-target").show();
        e.preventDefault();
    }
});

$("#drop-target").on('dragenter', function (e) {
    if (is_file(e)) {
        e.preventDefault();
        reset_msg();
        d = $("#drop-message");
        d.text("Drop image anywhere to upload");
        d.prop("class", "alert alert-info")
        d.show();
    }
});

$("#drop-target").on('dragleave', function (e) {
    if (is_file(e)) {
        e.preventDefault();
        reset_msg();
        $("#drop-target").hide();
    }
});

$("#drop-target").on('dragover', function (e) {
    if (is_file(e)) { e.preventDefault(); }
});

$("#drop-target").on('drop', function (e) {
    if (is_file(e)) {
        e.preventDefault();
        $("#drop-target").hide();
        reset_msg();

        filename = e.originalEvent.dataTransfer.files[0].name;

        var fd = new FormData();
        fd.append('file', e.originalEvent.dataTransfer.files[0]);
        fd.append('filename', filename);

        d = $("#drop-message");

        $.ajax({
            type: 'POST',
            url: upload_path,
            data: fd,
            processData: false,
            contentType: false
        })
            .done(function () {
                d.text("Image uploaded successfully.");
                d.prop("class", "alert alert-success")
            }).fail(function () {
                d.text("Error uploading image.");
                d.prop("class", "alert alert-danger")
            }).always(function () {
                d.show();
                drop_timeout = setTimeout(function () { d.fadeOut(); }, 1000);
            });

    }
});