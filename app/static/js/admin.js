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
            page: this.page
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
    console.log(this.gameCache);
    console.log(this.matchCache);
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

    this.matchCache = {};
    this.gameCache = {};
    this.teamCache = {};

    $.get("/admin/api/team/list", (function (data) {
        this.teamCache = data.teams;
    }).bind(this));

    $.when(
        $.get("/admin/api/match/list", (function (data) {
            this.matchCache = data.matches;
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
    $("#match-modal-location").empty().html(this.app.render("admin_match_modal", {
        match: match,
        games: this.gameCache,
        teams: this.teamCache,
        create: false
    }));
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

admin.route("/admin/matches", function () {
    this.loadMatches();

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
        this.saveMatchDraft();
    }).bind(this));
})

