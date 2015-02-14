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

                if (data.id == this.app.user.id) {
                    this.renderBetHistory(data.bets.detail);
                }
            }
        }).bind(this)
    });
}).bind(profile);

profile.renderBackgroundImage = (function (data) {
    var test = new Trianglify();
    var pattern = test.generate($(".bg-cover").width(), $(".bg-cover").height());

    $(".bg-cover").css("background-image", 'url(' + pattern.dataUri + ')');
}).bind(profile);

profile.renderBetHistory = (function (data) {
    _.each(data, (function (item) {
        $(".bet-history").append(this.app.render("past_bet", {
            bet: item
        }));
    }).bind(this));
}).bind(profile);

