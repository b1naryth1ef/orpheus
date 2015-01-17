var home = app.view("home");

home.route("/", function () {
    console.log(this);
    console.log(this.app.templates);
    $(".content-wrapper").append(this.app.render("frontpage_match", {}));
});
