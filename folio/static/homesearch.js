$("#wiki-search").on("keyup", function(e) {
    if (e.code == "Enter" & $("#wiki-search").val().length) {
        window.location = $("#wiki-listing").children().find("a")[0].href;
    } else {
        $.get(
            "/wikititles/" + $("#wiki-search").val()
        ).done(function(data) {
            $("#wiki-listing").replaceWith(data);
        });
    }
});
$("#wiki-search").focus();