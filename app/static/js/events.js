var events = app.view("events");

events.loadMatches = function(id) {
    var renderMatchesFromData = (function (data) {
        $(".matches-container").empty();
        
        _.each(data.matches, (function (item) {
            $(".matches-container").append(this.app.render("match_frontpage", {
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
    
    var params = {};
    
    params.active = "true";

    $.ajax("/api/events/list", {
        type: 'POST',
        data: params,
        success: renderEventsFromData
    })
}

events.renderMatches = function () {
    var renderMatchesFromData = (function (data) {
        $(".matches-container").empty();
        
        _.each(data.matches, (function (item) {
            $(".matches-container").append(this.app.render("match_frontpage", {
                match: item
            }));
        }).bind(this));
    }).bind(this);
    
    $.ajax("/api/match/list", {
        success: renderMatchesFromData
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
    this.loadMatches(id);
    
    this.renderEvents();

    $(".events-container").delegate(".event-row", "click", (function (ev) {
        var eventID = $(ev.target).closest(".event-row").attr("data-id");
        window.location = "/event/" + eventID;
    }).bind(this));
});

/*
admin.loadMatches = (function () {
    this.page = this.page || 1;
    this.max_pages = 0;

    this.teamCache = {};
    this.matchCache = {};
    this.gameCache = {};
    this.eventCache = {};

    // Get all the things
    $.when(
        $.get("/admin/api/team/list", (function (data) {
            this.teamCache = data.teams;
        }).bind(this)),

        $.get("/admin/api/match/list", (function (data) {
            this.matchCache = data.matches;
        }).bind(this)),

        $.get("/admin/api/event/list", {active: true}, (function (data) {
            this.eventCache = data.events;
        }).bind(this)),

        $.get("/admin/api/game/list", (function (data) {
            this.gameCache = data.games;
        }).bind(this))
    ).then((function () {
        this.renderMatches();
    }).bind(this));
}).bind(admin);

var home = app.view("home");

home.renderMatches = function () {
    var renderMatchesFromData = (function (data) {
        // Clear previous matches listed
        $(".matches-container").empty();

        _.each(data.matches, (function (item) {
            $(".matches-container").append(this.app.render("match_frontpage", {
                match: item
            }));
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
*/