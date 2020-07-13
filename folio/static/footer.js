var drop_timeout;

function reset_msg() {
    clearTimeout(drop_timeout);
    d = $("#drop-message")
    d.stop().animate({ opacity: '100' });
    d.text("");
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
    d.prop("class", "drop-message alert alert-" + css_class)
    d.show();
    clearTimeout(drop_timeout);
    if (timeout > 0) {
        drop_timeout = setTimeout(function () { d.fadeOut(); }, timeout);
    }
    else {
        d.html(d.html() + "<p><a href='#' onclick='d=$(\"#drop-message\");d.hide();d.html(\"\");' class='small'>Close this message</a></p>")
    }
}

function is_file(e) {
    return e.originalEvent.dataTransfer.types[0] == "Files";
}

function handleImagePaste(e) {
    var cd = (e.clipboardData || e.originalEvent.clipboardData);
    var items = cd.items;
    item = items[0];
    valid = false;
    if (item!=undefined && item.kind === 'file'){
        e.preventDefault();
        valid = true;
        var blob = item.getAsFile();
        console.log(blob);
        
        var reader = new FileReader();
        reader.readAsDataURL(blob);
        
        var formData = new FormData();
        formData.append("file", blob, blob.name)
        
        console.log(formData);
        $.ajax({
          type: "POST",
          url: mediaPaste,
          data: formData,
          contentType: false,
          processData: false,
          success: function(data) {
            txt = data.split('\n')            
            show_msg("<div class='media'><a target='_blank' href='"+txt[1]+"'><img src='"+txt[0]+"'></a><div class='media-body'><p>Pasted image of " + blob.size + " bytes.<br/><a target='_blank' href='"+txt[1]+"'>Click here</a> to see the uploaded image.</p></div></div>", "alert alert-success", timeout = 0, html = true);
            if (documentInsert!=undefined){
                documentInsert(txt[2]);
            }
          }
        }
        );
    }
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

            show_msg('<div class="progress upload-progress"><div id="upload_progess" class="progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div></div>'+
            '<div id="upload_report"></div>', "success", timeout=0, html=true);
            report = $("#upload_report");

            file_counter = 0;
            progress_bar = $("#upload_progess");

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
                    .done(function (data) {
                        txt = data.split('\n');                        
                        report.html(report.html() + "<div class='media'><a target='_blank' href='"+txt[1]+"'><img src='"+txt[0]+"'></a><div class='media-body'>"+txt[2]+"</div></div>");
                        if (documentInsert!=undefined){
                            documentInsert(`![](${txt[2]})`);
                        }
                    })
                    .fail(function () {
                        report.html(report.html() + "<div>File " + file.name +" did not upload; may be too big or wrong type</div>");
                    })
                    .always(function () {
                        file_counter++;
                        total_progress = (file_counter/files.length)*100;
                        progress_bar.prop("aria-valuenow", total_progress);
                        progress_bar.css("width", total_progress+'%');
                        progress_bar.text(total_progress+'%');
                    });

            }

        }

    }
});

