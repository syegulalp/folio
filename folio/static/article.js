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