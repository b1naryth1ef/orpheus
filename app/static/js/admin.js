app.view("/admin/", true).attach(function () {
    console.log("hi.");
})

app.view("/admin/users", true).attach(function () {
    this.page = this.page || 1;

    $.ajax("/admin/api/user/list", {
        success: (function (data) {
            _.each(data.users, (function (user) {
                $("#users-content").append(this.app.render("admin_user_row", {user: user}))
            }).bind(this));
        }).bind(this)
    })
});
