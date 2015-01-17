/*
   This is an extremely simple JS view-route controller.
*/

var App = function () {
    this.templates = T || {};
    this.views = {};
    this.setup = null;
}

App.prototype.render = function (name, obj) {
    return this.templates[name](obj);
}

App.prototype.view = function (name) {
    this.views[name] = new View(this, name);
    return this.views[name];
}

App.prototype.run = function () {
    var url = '/' + window.location.pathname.substr(1);
    if (this.setup) { this.setup.call(this); }

    // Pattern match the route
    for (k in this.views) {
        for (match in this.views[k].routes) {
            if (match == url) {
                return this.views[k].call(match);
            }
        }
    }

    console.error("could not find router handler!");
}

var View = function (app, name) {
    this.app = app;
    this.name = name;
    this.routes = {};
    this.setup = null;
}

View.prototype.route = function (route, f) {
    this.routes[route] = f;
}

View.prototype.call = function (route) {
    if (this.setup) this.setup();
    return this.routes[route].call(this);
}

var app = new App();

app.setup = function () {
    $.ajax("/auth/info", {
        success: (function (data) {
            if (data.authed) {
                this.user = data.user;
                $(".authed").show();
            } else {
                this.user = null;
                $(".unauthed").show();
            }

            if (data.user.group === "super" || data.user.group === "admin") {
                $(".admin").show();
            }
        }).bind(this)
    });
};

