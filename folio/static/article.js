$(window).on("keydown", function (e) {
console.log("a")
if (e.ctrlKey) {
    console.log("b")
    if (e.code == 'KeyE') {
    console.log("OK")
    e.preventDefault();
    $('#article-edit-link')[0].click();
    }
}
});