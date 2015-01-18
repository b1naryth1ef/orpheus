var admin = app.view("admin");

admin.route("/admin/", function () {
    console.log("hi.");
})

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
                console.log(data)
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
