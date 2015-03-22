var events = app.view("events");

events.renderMatches = function(id) {
    var renderMatchesFromData = (function (data) {
        $(".events-container").empty();

        _.each(data.matches, (function (item) {
            $(".events-container").append(this.app.render("match_frontpage", {
                match: item
            }));
        }).bind(this));
    }).bind(this);

    $.ajax("/api/events/" + id + "/list", {
        success: renderMatchesFromData
    })
}

events.renderEvents = function () {
    var renderEventsFromData = (function (data) {
        $(".events-container").empty();

        _.each(data.events, (function (item) {
            $(".events-container").append(this.app.render("events_frontpage", {
                event: item
            }));
        }).bind(this));
    }).bind(this);

    $.ajax("/api/events/list", {
        type: 'POST',
        data: {
            active: true
        },
        success: renderEventsFromData
    })
}

events.route("/events", function () {
    this.renderEvents();

    $(".events-container").delegate(".event-row", "click", (function (ev) {
        var eventID = $(ev.target).closest(".event-row").attr("data-id");
        window.location = "/event/" + eventID;
    }).bind(this));
});

events.routeRegex(/^\/event\/(\d+)$/, function (route, id) {
    this.renderMatches(id);

    $(".events-container").delegate(".match-row", "click", (function (ev) {
        var eventID = $(ev.target).closest(".match-row").attr("data-id");
        window.location = "/match/" + eventID;
    }).bind(this));
});

