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
