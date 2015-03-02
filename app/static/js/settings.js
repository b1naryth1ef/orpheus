var settings = app.view("settings");

settings.route("/settings", function () {
    if (!this.app.user) {
        window.location = '/';
    }

    $(".settings-container").delegate(".settings-save", "click", (function (ev) {
        ev.stopImmediatePropagation();
        ev.preventDefault();
        this.onSave();
    }).bind(this));

    this.render();
});

settings.render = (function () {
    $(".settings-container").html(this.app.render("settings", this.app.user));
    this.onUpdate();
}).bind(settings);

settings.getKeyFromPath = function (obj, path) {
    var result = obj;
    path.split(".").map(function (item) {
        result = result[item];
    })

    return result
}

settings.onUpdate = (function () {
    $(".settings").each((function (index, el) {
        var value = this.getKeyFromPath(this.app.user.settings, $(el).attr("data-name"));
        if (value != undefined && value != null) {
            if (typeof value == 'boolean') {
                $(el).prop('checked', value);
            } else {
                $(el).val(value);
            }
        }
    }).bind(this));
}).bind(settings);

settings.onSave = (function () {
    var newSettings = {};
    $(".settings").each((function (index, el) {
        if ($(el).is(':checkbox')) {
            newSettings[$(el).attr('data-name')] = $(el).is(":checked");
        } else {
            newSettings[$(el).attr('data-name')] = $(el).val();
        }
    }).bind(this));

    $.ajax("/api/user/settings/save", {
        type: 'POST',
        data: {
            'data': JSON.stringify(newSettings)
        },
        success: (function (data) {
            if (data.success) {
                $.ajax("/api/flash", {
                    data: {
                        msg: "Settings Saved",
                    },
                    success: function () {
                        window.location = '/settings';
                    }
                });
            } else {
                $.notify("Error saving settings: " + data.message, "danger");
            }
        }).bind(this)
    });
}).bind(settings);

