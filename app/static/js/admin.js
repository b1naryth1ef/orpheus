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

    $("#btn-search").click((function (eve) {
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

    $("#games-content").delegate(".game-edit", "click", (function (eve) {
        var id =  $($(eve.target).parents()[1]).attr("data-id");
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
                success: (function (eve) {
                    if (eve.success) {
                        this.loadGames();
                        $("#game-modal").modal("hide");
                        $.notify("Game created!", "success");
                    } else {
                        $.notify("Error creating game: " + eve.message, "danger");
                    }
                }).bind(this)
            });
        } else {
            data["game"] = $(form).attr("data-id");
            $.ajax("/admin/api/game/edit", {
                data: data,
                type: "POST",
                success: (function (eve) {
                    if (eve.success) {
                        this.loadGames();
                        $("#game-modal").modal("hide");
                        $.notify("Game saved!", "success");
                    } else {
                        $.notify("Error saving game: " + eve.message, "danger");
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
    console.log(match);
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

admin.saveMatch = (function (eve) {
    var id = $($(eve.target).parents()[2]).attr("data-id");
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

    $("#match-add-button").click((function (eve) {
        $("#match-modal").modal("hide");
        console.log(this.eventCache);
        $("#match-modal-location").empty().html(this.app.render("admin_match_entry", {
            games: this.gameCache,
            teams: this.teamCache,
            events: this.eventCache,
            create: true,
        }));
        setupDateFields();
        $("#match-modal").modal("show");
    }).bind(this));

    $("#matches-table").delegate(".match-edit", "click", (function (eve) {
        eve.stopImmediatePropagation();
        var matchRow = $(eve.target).parent().parent();
        this.renderSingleMatchEntry(this.matchCache[matchRow.attr("data-id")]);
    }).bind(this));

    $("#matches-table").delegate(".match-draft", "click", (function (eve) {
        eve.stopImmediatePropagation();
        var matchRow = $(eve.target).parent().parent();
        this.renderMatchDraft(this.matchCache[matchRow.attr("data-id")]);
    }).bind(this));

    $("#match-modal-location").delegate("#match-draft-save", "click", (function (eve) {
        eve.stopImmediatePropagation();
        this.saveMatchDraft();
    }).bind(this));

    $("#match-modal-location").delegate("#match-save", "click", (function (eve) {
        eve.stopImmediatePropagation();
        this.saveMatch(eve);
    }).bind(this));
})

admin.saveTeam = (function (eve) {
    var id = $($(eve.target).parents()[2]).attr("data-id");
    var data = _.reduce(_.map($(".team-field"), function (el) {
        var val = {};
        val[$(el).attr("data-name")] = getDataFromField(el);
        return val
    }), function (a, b) { return _.extend(a, b) });

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
    console.log(team);
    $("#team-modal-location").empty().html(this.app.render("admin_team_entry", {
        team: team,
        create: false,
    }));
    setupDateFields();
    $("#team-modal").modal("show");
}).bind(admin);

admin.route("/admin/teams", function () {
    this.loadTeams();

    $("#team-add-button").click((function (eve) {
        $("#team-modal").modal("hide");
        console.log(this.eventCache);
        $("#team-modal-location").empty().html(this.app.render("admin_team_entry", {
            create: true,
        }));
        setupDateFields();
        $("#team-modal").modal("show");
    }).bind(this));

    $("#teams-table").delegate(".team-edit", "click", (function (eve) {
        eve.stopImmediatePropagation();
        var teamRow = $(eve.target).parent().parent();
        this.renderSingleTeamEntry(this.teamCache[teamRow.attr("data-id")]);
    }).bind(this));

    $("#team-modal-location").delegate("#team-save", "click", (function (eve) {
        eve.stopImmediatePropagation();
        this.saveTeam(eve);
    }).bind(this));
})