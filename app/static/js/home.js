
app.view("/").attach(function () {
    console.log(this);
    console.log(this.app.templates);
    $(".content-wrapper").append(this.app.render("frontpage_match", {}));
})
