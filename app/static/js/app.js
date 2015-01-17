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

App.prototype.view = function (route) {
    this.views[route] = new View(this, route);
    return this.views[route];
}

App.prototype.run = function () {
    var parser = document.createElement('a');
    parser.href = window.location.pathname.substr(1);

    if (this.setup) { this.setup.call(this); }

    // Special index-page case
    if (!parser.pathname || parser.pathname === "/") {
        if (this.views["/"]) {
            return this.views["/"].call();
        }
    }

    // Pattern match the route
    for (k in this.views) {
        var q = parser.pathname.match(new RegExp(k));
        if (q && q.length) {
            return this.views[k].call();
        }
    }

    console.error("could not find router handler!");
}

var View = function (app, route) {
    this.app = app;
    this.route = route;
    this.handler = null;
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
        }).bind(this)
    });
};

