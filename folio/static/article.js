$(window).on("keydown", function (e) {
if (e.ctrlKey) {
    if (e.code == 'KeyE') {
    e.preventDefault();
    $('#article-edit-link')[0].click();
    }
}
});