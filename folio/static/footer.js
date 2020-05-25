var drop_timeout;

function reset_msg() {
    clearTimeout(drop_timeout);
    d = $("#drop-message")
    d.stop().animate({ opacity: '100' });
    d.hide();
}

function show_msg(text, css_class, timeout = 3000, html = false) {
    d = $("#drop-message");
    if (html) {
        d.html(text);
    }
    else {
        d.text(text)
    }
    d.prop("class", "alert alert-" + css_class)
    d.show();
    clearTimeout(drop_timeout);
    if (timeout > 0) {
        drop_timeout = setTimeout(function () { d.fadeOut(); }, timeout);
    }
    else {
        d.html(d.html() + "<p><a href='#' class='small'>Close this message</a></p>")
    }
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

        var files = e.originalEvent.dataTransfer.files;

        if (files.length > 0) {

            var status = true

            for (var i = 0; i < files.length; i++) {
                file = files[i];
                console.log(file);

                var fd = new FormData();
                fd.append('file', file);
                fd.append('filename', file.name);

                d = $("#drop-message");

                $.ajax({
                    type: 'POST',
                    url: upload_path,
                    data: fd,
                    processData: false,
                    contentType: false
                })
                    .done(function () { })
                    .fail(function () {
                        status = false
                    })
                    .always(function () { });

            }

            if (status) {
                show_msg(files.length + " files uploaded successfully.<br><a href='"+media_path+"'>Click here to view uploads.</a>", "success", timeout=0, html=true)
            }
            else {
                show_msg("Some files did not upload.", "danger")
            }

        }

    }
});