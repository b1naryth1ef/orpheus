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
                $(".profile-container").html(this.app.render("profile_page", {user: data}));
                this.renderBackgroundImage(data);

                if (data.id == this.app.user.id) {
                    this.renderBetHistory(data.bets.detail);
                    this.renderReturns();
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

profile.renderReturns = (function () {
    $.get("/api/returns/list", (function (data) {
        if (data.returns.length) {
            $("[fort-place=returns]").html(this.app.render("profile_returns", {
                returns: data.returns
            }));
        }
    }).bind(this));
}).bind(profile);

profile.renderBetHistory = (function (data) {
    _.each(data, (function (item) {
        console.log(item);
        $("[fort-place=history]").append(this.app.render("profile_past_bet", {
            bet: item
        }));
    }).bind(this));
}).bind(profile);

