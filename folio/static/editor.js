var keyTimer;

function setDirty() {
    $('#save-form').data("dirty", "true");
}

function clearDirty() {
    $('#save-form').data("dirty", "false");
}

function resizeEditor() {
    if (hasError) {
        $("#save-button").prop("type", "submit");
    }
    $('#article_content').height(
        window.innerHeight
        - $('#left-col')[0].offsetTop
        - $('#editor-text')[0].offsetTop
        - $('#editor-buttons')[0].clientHeight
        - 32
    )
        ;
}
function togglePreview() {
    $('#mid-col').toggle();
    if ($('#mid-col').css('display') == 'none') {
        $('#left-col').attr('class', 'col');
        $('#mid-col').attr('class', '');
    } else {
        $('#left-col').attr('class', 'col');
        $('#mid-col').attr('class', 'col');
        loadPreview();
    }
    resizeEditor();
}

function loadPreview() {
    if ($('#mid-col').css('display') == 'none') return false;
    $.ajax({
        url: previewTarget,
        dataType: "html"
    }).done(function (data) {
        updatePreview(data);
    })
}

function synchPreviewScroll() {
    preview = $('#mid-col')[0];
    editor = $("#article_content")[0];
    pos = editor.scrollTop / (editor.scrollHeight - editor.clientHeight);
    preview.scrollTop = (preview.scrollHeight - preview.clientHeight) * pos;
}

function updatePreview(data) {
    $('#mid-col').html(data);
    synchPreviewScroll();
}

function ajaxSave() {
    var form = $('#save-form')[0];
    var data = new FormData(form);

    $.ajax({
        type: "POST",
        url: saveTarget,
        data: data,
        contentType: false,
        processData: false,
        success: function (data) {
            clearDirty();
            $('#flash-message').html(data);
            $('#flash-message').fadeIn();
            setTimeout(function () { $('#flash-message').fadeOut() }, 3000);
            loadPreview();
        },
        error: function(data){
            clearDirty();
            $('#flash-message').html('<div class="alert-box alert alert-warning">Error saving document. (Is the app still running?)</div>');
            $('#flash-message').fadeIn();
        },
        complete: function () {
        }
    });
}

function hasSelection(field) {
    return field.selectionEnd-field.selectionStart;
}


function wrapText(field, left, right) {
    
    start = field.selectionStart;
    end = field.selectionEnd;

    selection = left + field.value.substring(start, end) + right;

    document.execCommand('insertText', false, selection);

    if (start == end) {
        field.selectionStart = field.selectionEnd = end + left.length;
    } else {
        field.selectionStart = start + left.length;
        field.selectionEnd = end + left.length;
    }
}

function documentAddBold() {
    wrapText($("#article_content")[0], '**', '**');
}

function documentAddItalic() {
    wrapText($("#article_content")[0], '*', '*');
}

function openModal(destination) {
    $.ajax({
        url: articleTarget + '/' + destination,
        dataType: "html"
    }).done(function (data) {
        $('#edit-modal').html(data);
        $('#edit-modal').modal();
        modalPostLoad();
    })
}

function insertImage(item) {
    $('#edit-modal').modal('hide');
    $("#article_content").focus();
    document.execCommand("insertText", false, '![](' + $(item).data("url") + ')');
}

function tagEnter() {
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

function insertLink(item) {
    linkText = $(item).html();
    linkAltText = $("#modal-alt-input").val();

    $("#article_content").focus();
    field = $("#article_content")[0];
    if (hasSelection(field)) {
        wrapText(field, '[', ']('+linkText+')')
    }
    else    
    {
        if (linkAltText.length == 0) {
            wrapText(field, '[['+linkText+']]','')
        }
        else {
            wrapText(field, '['+linkAltText+']','('+linkText+')')
        }        
    }
    $('#edit-modal').modal('hide');
}

function insertTag(item) {
    $.post(
        articleTarget + "/add-tag",
        { tag: $(item).html() }
    ).done(function (data) {
        $('#modal-tag-listing').html(data);
    })
}

function removeTag(item) {
    $.post(
        articleTarget + "/remove-tag",
        { tag: $(item).html() }
    ).done(function (data) {
        $('#modal-tag-listing').html(data);
    })
}

function setEnterEvent(item) {
    item.on("keydown", function (e) {
        if (e.originalEvent.key === "Enter") {
            e.preventDefault();
            if (!e.originalEvent.shiftKey) {
                if (!$("#modal-search-results a").length) {
                    modalPostEnter();
                } else {
                    $("#modal-search-results a")[0].click();
                }
            }
            else {
                modalPostEnter();
            }
            $("#modal-search-query").val('');
        }
    });
}

function document_ready(){
    resizeEditor();
    $("#article_content").focus();
}

$(document).ready(document_ready);
$(window).on('resize', resizeEditor);

$('#btn_toggle_preview').on("click", togglePreview);

$('#btn_toggle_bold').on("click", function () {
    documentAddBold();
});

$('#btn_toggle_ital').on("click", function () {
    documentAddItalic();
});

$("#article_content").on("scroll", synchPreviewScroll);

$("#save-button").on("click", function () {
    if ($("#save-button").prop("type") === "button") {
        ajaxSave();
    }
});

$("#article_title").on("change", function (e) {
    setDirty();
});

$("#article_title").on("keypress", function (e) {

    btn = $("#save-button");
    title = $("#article_title");

    if (title.data("original") != title.val()) {
        btn.prop("type", "submit");
    }
    else {
        if (!hasError) {
            btn.prop("type", "button");
        }
    }

    if (e.originalEvent.keyCode === 13) {
        e.preventDefault();
        $("#save-button").click();

    }

});

$("#article_content").on("change", function (e) {
    setDirty();
});

$("#article_content").on("keydown", function (e) {
    if (e.code == 'Tab') {
        e.preventDefault();
        wrapText(this, '    ', '');
    }
    if (e.altKey) {
        if (e.shiftKey) {
            if (e.code == 'KeyS') {
                e.preventDefault();
                $("#save-and-publish-button").click();
            }
        }
    }

    // replace with switch/case

    if (e.ctrlKey) {
        if (e.code == 'KeyL') {
            e.preventDefault();
            $('#btn_insert_link').click();
        }        
        else if (e.code == 'KeyM') {
            if (e.shiftKey) {
                e.preventDefault();            
                $('#btn_edit_metadata').click();
            }
            else {
                e.preventDefault();            
                $('#btn_insert_media').click();
            }
        }      
        else if (e.code == 'KeyG') {
            e.preventDefault();
            $('#btn_insert_tag').click();
        }     
        else if (e.code == 'KeyP') {
            e.preventDefault();
            $('#btn_toggle_preview').click();
        }
        else if (e.code == 'KeyS') {
            if (e.shiftKey) {
                e.preventDefault();
                $("#save-and-exit-button").click();
            } else {
                e.preventDefault();
                $("#save-button").click();
            }
        }
        else if (e.code == 'KeyI') {
            e.preventDefault();
            documentAddItalic();
        }
        else if (e.code == 'KeyB') {
            e.preventDefault();
            documentAddBold();
        }
    }
});

$(window).on("beforeunload", function () {
    if ($('#save-form').data("dirty") === "true") {
        return false;
    }
})

$("#btn_insert_media").on("click", function () {
    openModal('insert-image');
});

$("#btn_insert_tag").on("click", function () {
    openModal('insert-tag');
});

$("#btn_edit_metadata").on("click", function () {
    openModal('edit-metadata')
});

$("#btn_insert_link").on("click", function () {
    openModal('insert-link')
});


// $("#article_content").on("keydown", function () {
//     clearTimeout(keytimer);
// });
// $("#article_content").on("keyup", function () {
//     keytimer = setTimeout(load_preview, 3000)
// });