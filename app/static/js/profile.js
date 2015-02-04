var profile = app.view("profile");


profile.route("/profile", function () {
    if (!this.app.user) {
        window.location = '/';
    }

    this.renderProfile(this.app.user.id);
});

profile.routeRegex(/^\/profile\/(\d+)$/, function (route, id) {
    this.renderProfile(id[0]);
})

profile.renderProfile = (function (id) {
    $.ajax("/api/user/" + id + "/info", {
        success: (function (data) {
            if (data.success) {
                $(".profile-container").html(this.app.render("profile", {user: data}));
                this.renderBackgroundImage(data);
            }
        }).bind(this)
    });
}).bind(profile);

profile.renderBackgroundImage = (function (data) {
    var test = new Trianglify();
    var pattern = test.generate($(".bg-cover").width(), $(".bg-cover").height());

    $(".bg-cover").css("background-image", 'url(' + pattern.dataUri + ')');
}).bind(profile);

