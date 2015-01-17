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

App.prototype.view = function (route, exact) {
    this.views[route] = new View(this, route, exact);
    return this.views[route];
}

App.prototype.run = function () {
    var url = '/' + window.location.pathname.substr(1);
    if (this.setup) { this.setup.call(this); }

    // Pattern match the route
    for (k in this.views) {
        if (k == url) {
            return this.views[k].call();
        }
    }

    console.error("could not find router handler!");
}

var View = function (app, route, exact) {
    this.app = app;
    this.route = route;
    this.handler = null;
    this.exact = exact || true;
}

View.prototype.attach = function (f) {
    this.handler = f;
}

View.prototype.call = function () {
    return this.handler.call(this);
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

