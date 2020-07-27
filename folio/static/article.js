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

function setArticle(data){
    new_ = $(data).find("#article-col")[0];
    $("#article-col").replaceWith(new_);
    console.log($(data).filter("title"));
    document.title = $(data).filter("title").text();
}

$('.jsnavlink').on('click', function(e) {
    e.preventDefault();
    href = this.href
    $.ajax({
        type: "GET",
        url: href,
        success: function(data){
            window.history.pushState({url: window.href}, null, href);
            setArticle(data);    
        }
    });   
});

window.addEventListener("popstate", function(e) {
    console.log(e.state);
    if (e.state != null) {
        e.preventDefault();
        href = e.state.url;
        $.ajax({
            type: "GET",
            url: href,
            success: function(data){
                setArticle(data);    
            }
        });    
    } else
    {
        window.location.href = window.location.href;
    }
});