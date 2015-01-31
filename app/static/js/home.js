var home = app.view("home");

home.renderMatches = function () {
    var renderMatchesFromData = (function (data) {
        // Clear previous matches listed
        $(".matches-container").empty();

        _.each(data.matches, (function (item) {
            $(".matches-container").append(this.app.render("frontpage_match", {match: item}));
        }).bind(this));
    }).bind(this);

    $.ajax("/api/match/list", {
        success: renderMatchesFromData
    })
}

home.route("/", function () {
    this.renderMatches();

    $(".matches-container").delegate(".match-row", "click", (function (ev) {
        var matchID = $(ev.target).closest(".match-row").attr("data-id");
        window.location = "/match/" + matchID;
    }).bind(this));
});

