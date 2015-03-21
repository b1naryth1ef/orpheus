var admin = app.view("admin");

admin.route("/admin/", function () {})

admin.renderSingleUserRow = (function (user) {
    $("#users-content").append(this.app.render("admin_user_row", {user: user, hidden: true}));
    $(".user-row:hidden").fadeIn();
}).bind(admin);

admin.loadUsers = (function () {
    this.page = this.page || 1;
    this.max_pages = 0;
    this.usersCache = {};

    $("#users-page-current").text(this.page);
    $("#users-content").empty();

    $.ajax("/admin/api/user/list", {
        data: {
            page: this.page,
            query: this.query
        },
        success: (function (data) {
            _.each(data.users, (function (user) {
                this.usersCache[user.id] = user;
                this.renderSingleUserRow(user);
            }).bind(this));
            this.max_pages = data.pages;
        }).bind(this)
    });
}).bind(admin);

admin.renderSingleUserEntry = (function (user) {
    $("#edit-users-modal").modal("hide");
    var loc = $("#user-modal-location").empty().html(
            this.app.render("admin_user_entry", {user: user}));
    $("#edit-user-modal").modal("show");
}).bind(this);

admin.route("/admin/users", function () {
    this.query = "";
    this.loadUsers();

    $("#users-page-last").click((function () {
        if (this.page > 1) {
            this.page--;
            this.loadUsers();
        }
    }).bind(this));

    $("#users-page-next").click((function () {
        if (this.page < this.max_pages) {
            this.page++;
            this.loadUsers();
        }
    }).bind(this));

    $("#btn-search").click((function (ev) {
        this.query = $("#search-box").val();
        this.loadUsers();
    }).bind(this));

    $("#refresh-users").click(this.loadUsers);

    $("#users-table").delegate(".user-edit", "click", (function (ev) {
        ev.stopImmediatePropagation();

        var userRow = $(ev.target).parent().parent();
        this.renderSingleUserEntry(this.usersCache[userRow.attr("data-uid")]);
    }).bind(this));

    $("#user-modal-location").delegate(".user-edit-save", "click", (function (ev) {
        ev.stopImmediatePropagation();
        $("#edit-user-error").hide();

        // TODO: cleanup plz

        var params = {};
        params.user = $($(ev.target).parents()[2]).attr("data-uid");
        params.active = $("#user-edit-active").is(":checked");
        params.ugroup = $("#user-ugroup").val();

        var user = this.usersCache[params.user];

        if (params.active == user.active) {
            params.active = undefined;
        }

        $.ajax("/admin/api/user/edit", {
            type: 'POST',
            data: params,
            success: (function (data) {
                if (!data.success) {
                    $("#edit-user-error").fadeIn();
                    $("#edit-user-error").text(data.message);
                } else {
                    $("#edit-user-modal").modal("hide");
                    $.notify("User saved!", "success");
                    this.loadUsers();
                }
            }).bind(this)
        })
    }).bind(this));
});

admin.route("/admin/bans", function () {
    this.loadBans();
    $("#bans-page-last").click((function() {
        if (this.page > 1) {
            this.page--;
            this.loadBans();
        }
    }).bind(this));


    $("#bans-page-next").click((function() {
        if (this.page < this.max_pages) {
            this.page++;
            this.loadBans();
        }
    }).bind(this));

    $("#bans-content").delegate(".ban-edit", "click", (function (eve) {
        var id =  $($(eve.target).parents()[1]).attr("data-id");
        $("#ban-modal-location").html(this.app.render("admin_ban_modal", {
            create: false,
            ban: this.bansCache[id],
        }));
        setupDateFields();
        $("#ban-modal").modal("show");
    }).bind(this));


    $("#ban-add-button").click((function() {
        $("#ban-modal-location").html(this.app.render("admin_ban_modal", {
            create: true,
            ban: null
        }));
        setupDateFields();
        $("#ban-modal").modal("show");
    }).bind(this));

    $("#btn-search").click((function() {
    }).bind(this));

    $("#ban-modal-location").delegate("#ban-save", "click", (function (ev) {
        var form = $(ev.target).parents()[2];

        data = {};

        $(".ban-field").each((function (index, item) {
            if(item.type == "checkbox"){
                data[$(item).attr("data-name")] = $(item).prop("checked");
            } else if($(item).hasClass("date-field")){
                data[$(item).attr("data-name")] = $(item).data("date");
            } else {
                data[$(item).attr("data-name")] = $(item).val();
            }
        }).bind(this)).bind(this);

        if($(form).attr("data-id") == "create"){
            $.ajax("/admin/api/ban/create", {
                data: data,
                type: "POST",
                success: (function(eve){
                    if(eve.success){
                        $("#ban-modal").modal("hide");
                        $.notify("Ban saved", "success");
                        this.loadBans();
                    } else {
                        $.notify("Error saving ban: " + eve.message, "danger");
                    }
                }).bind(this)
            });
        } else {
            $.ajax("/admin/api/ban/edit", {
                data: data,
                type: "POST",
                success: (function(eve){
                    this.loadBans();
                }).bind(this)
            });

            $("#ban-modal").modal("hide");
        }


    }).bind(this));

});

admin.loadBans = function() {
    this.page = this.page || 1;
    this.max_pages = 0;
    this.bansCache = {};

    $("#bans-page-current").text(this.page);
    $.ajax("/admin/api/ban/list", {
        data: {
            page: this.page,
        },
        success: (function (data) {
            $("#bans-content").empty();
            _.each(data.bans, (function (v) {
                this.bansCache[v.id] = v;
                $("#bans-content").append(this.app.render("admin_ban_row", {
                    ban: v,
                    hidden: true,
                }));
                this.max_pages = data.pages;
                $(".ban-row:hidden").fadeIn();
            }).bind(this));
        }).bind(this)
    });
}

admin.loadGames = function () {
    this.page = this.page || 1;
    this.max_pages = 0;
    this.gamesCache = {};

    $.ajax("/admin/api/game/list", {
        success: (function (data) {
            $("#games-content").empty();
            _.each(data.games, (function (v) {
                this.gamesCache[v.id] = v;
                $("#games-content").append(this.app.render("admin_game_row", {
                    game: v,
                    hidden: true,
                }));
                $(".game-row:hidden").fadeIn();
            }).bind(this));
        }).bind(this)
    });
}

admin.route("/admin/games", function () {
    this.loadGames();

    $("#game-add-button").click((function () {
        $("#game-modal-location").html(this.app.render("admin_game_modal", {
            create: true,
            game: null
        }));
        $("#game-modal").modal("show");
    }).bind(this));

    $("#games-content").delegate(".game-edit", "click", (function (ev) {
        var id =  $($(ev.target).parents()[1]).attr("data-id");
        $("#game-modal-location").html(this.app.render("admin_game_modal", {
            create: false,
            game: this.gamesCache[id],
        }));
        $("#game-modal").modal("show");
    }).bind(this));

    $("#game-modal-location").delegate("#game-save", "click", (function (ev) {
        var form = $(ev.target).parents()[2],
        data = {};

        $(".game-field").each((function (index, item) {
            if (item.type == "checkbox") {
                data[$(item).attr("field-name")] = $(item).prop("checked");
            } else {
                data[$(item).attr("field-name")] = $(item).val();
            }
        }).bind(this));

        if ($(form).attr("data-mode") == "create") {
            $.ajax("/admin/api/game/create", {
                data: data,
                type: "POST",
                success: (function (ev) {
                    $("#game-modal").modal("hide");
                    if (ev.success) {
                        this.loadGames();
                        $.notify("Game created!", "success");
                    } else {
                        $.notify("Error creating game: " + ev.message, "danger");
                    }
                }).bind(this)
            });
        } else {
            data["game"] = $(form).attr("data-id");
            $.ajax("/admin/api/game/edit", {
                data: data,
                type: "POST",
                success: (function (ev) {
                    $("#game-modal").modal("hide");
                    if (ev.success) {
                        this.loadGames();
                        $.notify("Game saved!", "success");
                    } else {
                        $.notify("Error saving game: " + ev.message, "danger");
                    }
                }).bind(this)
            });
        }
    }).bind(this));
})


admin.restGetMatchList = (function () {
    return $.ajax("/admin/api/match/list");
}).bind(admin)

admin.renderMatches = (function () {
    $("#matches-content").empty();
    for (mid in this.matchCache) {
        $("#matches-content").append(this.app.render("admin_match_row", {
            match: this.matchCache[mid],
            games: this.gameCache,
            hidden: true
        }));

        $(".match-row:hidden").fadeIn();
    }
}).bind(admin)

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

admin.renderSingleMatchEntry = (function (match) {
    $("#match-modal").modal("hide");
    $("#match-modal-location").empty().html(this.app.render("admin_match_entry", {
        match: match,
        games: this.gameCache,
        teams: this.teamCache,
        events: this.eventCache,
        create: false,
    }));
    setupDateFields();
    $("#match-modal").modal("show");
}).bind(admin);

admin.renderMatchDraft = (function (match) {
    $("#match-modal").modal("hide");
    $("#match-modal-location").empty().html(this.app.render("admin_match_results", {
        match: match,
        games: this.gameCache,
        teams: this.teamCache,
    }));
    $("#match-modal").modal("show");
}).bind(admin);

admin.saveMatchDraft = (function () {
    var id = $("#match-modal").attr("data-id");
    var data = {};

    data.id = id;
    data.winner = $("#field-winner").val();
    data.state = $('input:radio[name=state]:checked').val();
    data.meta = [];

    for (i in _.range(5)) {
        if ($("#meta-type-" + i).val() != "Empty") {
            data.meta.push({
                type: $("#meta-type-" + i).val(),
                value: $("#meta-value-" + i).val()
            })
        }
    }

    data.results = {final: {}};

    $(".field-score").each((function (index, item) {
        var teamid = $(item).attr('id');
        var mapplayed = $(item).attr('map');

        if (data.results.final[mapplayed] === undefined) {
            data.results.final[mapplayed] = {};
        }

        if(data.results.final[mapplayed][teamid] === undefined) {
            data.results.final[mapplayed][teamid] = {};
        }

        data.results.final[mapplayed][teamid] = $(item).val();
    }).bind(this));

    $.ajax("/admin/api/match/results", {
        type: 'POST',
        data: JSON.stringify(data),
        dataType: 'json',
        contentType: "application/json; charset=utf-8",
        success: (function (data) {
            $("#match-modal").modal("hide");
            if (data.success) {
                $.notify("Match Result Saved", "success");
            } else {
                $.notify("Error: " + data.message, "danger");
            }
        })
    })
}).bind(admin);

admin.saveMatch = (function (ev) {
    var id = $($(ev.target).parents()[2]).attr("data-id");
    var data = _.reduce(_.map($(".match-field"), function (el) {
        var val = {};
        val[$(el).attr("data-name")] = getDataFromField(el);
        return val
    }), function (a, b) { return _.extend(a, b) });

    if (id) {
        var url = "/admin/api/match/" + id + "/edit";
    } else {
        var url = "/admin/api/match/create";
    }

    $.ajax(url, {
        type: 'POST',
        data: JSON.stringify(data),
        dataType: 'json',
        contentType: "application/json; charset=utf-8",
        success: (function (resp) {
            $("#match-modal").modal("hide");
            if (resp.success) {
                $.notify("Match Saved!", "success");
                this.loadMatches();
            } else {
                $.notify("Error: " + resp.message, "danger");
            }
        }).bind(this)
    });
}).bind(admin);

admin.route("/admin/matches", function () {
    this.loadMatches();

    $("#match-add-button").click((function (ev) {
        $("#match-modal").modal("hide");
        $("#match-modal-location").empty().html(this.app.render("admin_match_entry", {
            games: this.gameCache,
            teams: this.teamCache,
            events: this.eventCache,
            create: true,
        }));
        setupDateFields();
        $("#match-modal").modal("show");
    }).bind(this));

    $("#matches-table").delegate(".match-edit", "click", (function (ev) {
        ev.stopImmediatePropagation();
        var matchRow = $(ev.target).parent().parent();
        this.renderSingleMatchEntry(this.matchCache[matchRow.attr("data-id")]);
    }).bind(this));

    $("#matches-table").delegate(".match-draft", "click", (function (ev) {
        ev.stopImmediatePropagation();
        var matchRow = $(ev.target).parent().parent();
        this.renderMatchDraft(this.matchCache[matchRow.attr("data-id")]);
    }).bind(this));

    $("#match-modal-location").delegate("#match-draft-save", "click", (function (ev) {
        ev.stopImmediatePropagation();
        this.saveMatchDraft();
    }).bind(this));

    $("#match-modal-location").delegate("#match-save", "click", (function (ev) {
        ev.stopImmediatePropagation();
        this.saveMatch(ev);
    }).bind(this));
})

admin.saveTeam = (function (ev) {
    if (this.files) {
        this.uploadImage(this.files).done((function (data) {
            this.reallySaveTeam(ev, data)
        }).bind(this));
    } else {
        this.reallySaveTeam(ev);
    }
}).bind(admin);

admin.reallySaveTeam = (function (ev, formData) {
    var id = $($(ev.target).parents()[2]).attr("data-id");
    var data = _.reduce(_.map($(".team-field"), function (el) {
        var val = {};
        val[$(el).attr("data-name")] = getDataFromField(el);
        return val
    }), function (a, b) { return _.extend(a, b) });

    if (formData) {
        data.logo = formData.images[0]
    }

    if (id) {
        var url = "/admin/api/teams/" + id + "/edit";
    } else {
        var url = "/admin/api/teams/create";
    }

    $.ajax(url, {
        type: 'POST',
        data: JSON.stringify(data),
        dataType: 'json',
        contentType: "application/json; charset=utf-8",
        success: (function (resp) {
            $("#team-modal").modal("hide");
            if (resp.success) {
                $.notify("Team Saved!", "success");
                this.loadTeams();
            } else {
                $.notify("Error: " + resp.message, "danger");
            }
        }).bind(this)
    });
}).bind(admin);

admin.renderTeams = (function () {
    $("#teams-content").empty();
    for (team in this.teamCache) {
        $("#teams-content").append(this.app.render("admin_team_row", {
            team: this.teamCache[team],
            hidden: true
        }));

        $(".team-row:hidden").fadeIn();
    }
}).bind(admin)

admin.loadTeams = (function () {
    this.page = this.page || 1;
    this.max_pages = 0;

    this.teamCache = {};

    $.when(
            $.get("/admin/api/team/list", (function (data) {
                this.teamCache = data.teams;
            }).bind(this))
          ).then((function () {
        this.renderTeams();
    }).bind(this));
}).bind(admin);

admin.renderSingleTeamEntry = (function (team) {
    $("#team-modal").modal("hide");
    $("#team-modal-location").empty().html(this.app.render("admin_team_entry", {
        team: team,
        create: false,
    }));
    setupDateFields();
    $("#team-modal").modal("show");
}).bind(admin);

admin.route("/admin/teams", function () {
    this.loadTeams();

    $("#team-add-button").click((function (ev) {
        $("#team-modal").modal("hide");
        $("#team-modal-location").empty().html(this.app.render("admin_team_entry", {
            create: true,
        }));

        setupDateFields();

        $("#team-modal").modal("show");
    }).bind(this));

    $("#teams-table").delegate(".team-edit", "click", (function (ev) {
        ev.stopImmediatePropagation();
        var teamRow = $(ev.target).parent().parent();
        this.renderSingleTeamEntry(this.teamCache[teamRow.attr("data-id")]);
    }).bind(this));

    $("#team-modal-location").delegate("#team-save", "click", (function (ev) {
        ev.stopImmediatePropagation();
        this.saveTeam(ev);
    }).bind(this));

    $("#team-modal-location").delegate("#logo-field", "change", (function (ev) {
        this.files = event.target.files;
    }).bind(this));
})

admin.uploadImage = (function (files) {
    var data = new FormData()
    $.each(files, function (key, value) {
        data.append(key, value);
    });

    return $.ajax({
        url: "/admin/api/image/upload",
        type: "POST",
        data: data,
        cache: false,
        dataType: 'json',
        processData: false,
        contentType: false,
    });
})

admin.saveEvent = (function (ev, formData) {
    var id = $($(ev.target).parents()[2]).attr("data-id");
    var data = _.reduce(_.map($(".event-field"), function (el) {
        var val = {};
        val[$(el).attr("data-name")] = getDataFromField(el);
        return val
    }), function (a, b) { return _.extend(a, b) });

    if (formData) {
        _.each(formData.images, function (k, v) {
            data[v] = k;
        })
    }

    if (id) {
        var url = "/admin/api/events/" + id + "/edit";
    } else {
        var url = "/admin/api/events/create";
    }

    $.ajax(url, {
        type: 'POST',
        data: JSON.stringify(data),
        dataType: 'json',
        contentType: "application/json; charset=utf-8",
        success: (function (resp) {
            $("#event-modal").modal("hide");
            if (resp.success) {
                $.notify("Event Saved!", "success");
                this.loadEvents();
            } else {
                $.notify("Error: " + resp.message, "danger");
            }
        }).bind(this)
    });
}).bind(admin);

admin.renderEvents = (function () {
    $("#events-content").empty();

    for (event in this.eventCache) {
        $("#events-content").append(this.app.render("admin_event_row", {
            event: this.eventCache[event],
            hidden: true
        }));

        $(".event-row:hidden").fadeIn();
    }
}).bind(admin)

admin.loadEvents = (function () {
    this.eventCache = {};
    this.eventTypes = {};

    $.when(
            $.get("/admin/api/event/list", (function (data) {
                this.eventCache = data.events;
                this.eventTypes = data.eventtypes;
            }).bind(this))
          ).then((function () {
        this.renderEvents();
    }).bind(this));
}).bind(admin);

admin.renderSingleEventEntry = (function (ev) {
    $("#event-modal").modal("hide");
    $("#event-modal-location").empty().html(this.app.render("admin_event_entry", {
        event: ev,
        eventtypes: this.eventTypes,
        create: false,
    }));

    setupDateFields();

    $("#event-modal").modal("show");
}).bind(admin);

admin.route("/admin/events", function () {
    this.loadEvents();

    $("#event-add-button").click((function (ev) {
        $("#event-modal").modal("hide");
        $("#event-modal-location").empty().html(this.app.render("admin_event_entry", {
            eventtypes: this.eventTypes,
            create: true,
        }));
        setupDateFields();
        $("#event-modal").modal("show");
    }).bind(this));

    $("#events-table").delegate(".event-edit", "click", (function (ev) {
        ev.stopImmediatePropagation();
        var eventRow = $(ev.target).parent().parent();
        this.renderSingleEventEntry(this.eventCache[eventRow.attr("data-id")]);
    }).bind(this));

    $("#event-modal-location").delegate("#event-save", "click", (function (ev) {
        ev.stopImmediatePropagation();
        if (this.files) {
            this.uploadImage(this.files).done((function (data) {
                console.log(data);
                this.saveEvent(ev, data);
            }).bind(this));
        } else {
            this.saveEvent(ev);
        }
    }).bind(this));

    $("#event-modal-location").delegate(".image-field", "change", (function (ev) {
        this.files = this.files || {}
        this.files[$(ev.target).attr("data-name")] = ev.target.files[0];
        console.log(this.files);
    }).bind(this));
})

admin.route("/admin/news", (function () {
    this.renderNewsPosts();

    $("#news-add-button").click((function (ev) {
        $("#news-modal").modal("hide");

        $("#news-modal-location").empty().html(this.app.render("admin_news_entry", {
            create: true,
        })).bind(this);

        setupDateFields();

        $("#news-modal").modal("show");
    }).bind(this));

    $("#news-table").delegate(".news-edit", "click", (function (ev) {
        ev.stopImmediatePropagation();

        var newsPostID = ($(ev.target).parent().parent()).attr("data-id");
        this.renderSingleNewsPost(newsPostID);
    }).bind(this));

    $("#news-modal-location").delegate("#news-save", "click", (function (ev) {
        ev.stopImmediatePropagation();

        this.saveNewsPost(ev);
    }).bind(this));
}).bind(admin))

admin.renderSingleNewsPost = (function (id) {
    $.get("/api/news/" + id, (function (data) {
        $("#news-modal").modal("hide");

        $("#news-modal-location").empty().html(this.app.render("admin_news_entry", {
            create: false,
            news_post: data.post
        })).bind(this);

        setupDateFields();

        $("#news-modal").modal("show");
    }).bind(this));
}).bind(admin);

admin.renderNewsPosts = (function () {
    $.get("/api/news/list", (function (data) {
        $("#news-content").empty();

        _.each(data.posts, (function (post) {
            $("#news-content").append(this.app.render("admin_news_row", {
                hidden: true,
                news_post: post
            })).bind(this);

            $(".news-row:hidden").fadeIn();
        }).bind(this))
    }).bind(this));
}).bind(admin);

admin.saveNewsPost = (function (ev) {
    var newsPostID = $($(ev.target).parents()[2]).attr("data-id");

    var data = _.reduce(_.map($(".news-field"), function (field) {
        var values = {};

        if ($(field).attr("data-name") == "content") {
            values[$(field).attr("data-name")] = $(field).html();
        } else {
            values[$(field).attr("data-name")] = getDataFromField(field);
        }

        return values
    }), (function (a, b) { return _.extend(a, b) }).bind(this));

    if (newsPostID) {
        var url = "/admin/api/news/" + newsPostID + "/edit";
        data.id = newsPostID;
    } else {
        var url = "/admin/api/news/create";
    }

    $.ajax(url, {
        type: 'POST',
        data: JSON.stringify(data),
        dataType: 'json',
        contentType: "application/json; charset=utf-8",
        success: (function (data) {
            $("#news-modal").modal("hide");

            if (data.success) {
                $.notify("News Post Saved!", "success");

                this.renderNewsPosts();
            } else {
                $.notify("Error: " + data.message, "danger");
            }
        }).bind(this)
    });
}).bind(admin);

