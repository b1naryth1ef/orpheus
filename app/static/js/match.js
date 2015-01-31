var match = app.view("match");

match.renderSingleMatch = function (id) {
    $.ajax("/api/match/" + id + "/info", {
        success: (function (data) {
            console.log(data.match);
            $(".matches-container").html(this.app.render("single_match", {
                match: data.match,
                time: moment.unix(data.match.when),
            }));
        }).bind(this)
    });
}

match.routeRegex(/^\/match\/(\d+)$/, function (route, id) {
    this.renderSingleMatch(1);
});
