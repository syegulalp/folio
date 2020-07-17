$(window).on("keydown", function (e) {
    if (e.ctrlKey) {
        if (e.shiftKey) {
            if (e.code == 'KeyF') {
                e.preventDefault();
                $('#wiki_search_link')[0].click();
            }
        }
        if (e.code == 'KeyE') {
            e.preventDefault();
            $('#article-edit-link')[0].click();
        }
    }
});


$('.jsnavlink').on('click', function(e) {
    e.preventDefault();
    href = this.href
    $.ajax({
        type: "GET",
        url: href,
        success: function(data){
            window.history.pushState({}, null, href);
            new_ = $(data).find("#article-col")[0];
            $("#article-col").replaceWith(new_);
            console.log($(data).filter("title"));
            document.title = $(data).filter("title").text();
        }
    });   
});