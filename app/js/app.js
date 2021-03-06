/*
    This is an extremely simple JS view-route controller.
*/

var App = function () {
    this.templates = T || {};
    this.views = {};
    this.setup = null;
    this.socketEventHandlers = {};
    this.currentView = null;
}

App.prototype.waitForEvent = function (name, f) {
    if (this.socketEventHandlers[name]) {
        this.socketEventHandlers[name].push(f)
    } else {
        this.socketEventHandlers[name] = [f]
    }
}

App.prototype.render = function (name, obj) {
    obj.app = this;

    if (!this.templates[name]) {
        console.error("Failed to find template with name: " + name);
        return "";
    }
    return this.templates[name](obj);
}

App.prototype.view = function (name) {
    this.views[name] = new View(this, name);
    return this.views[name];
}

App.prototype.run = function () {
    var url = '/' + window.location.pathname.substr(1);

    // Pattern match the route
    for (k in this.views) {
        for (match in this.views[k].routes) {
            var regEx = this.views[k].routes[match]._regex;
            if (regEx) {
                var regMatch = url.match(regEx);
                if (regMatch) {
                    regMatch.shift();
                    this.currentView = this.views[k];
                    return this.views[k].call(match, regMatch);
                }
            } else if (match == url) {
                this.currentView = this.views[k];
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

View.prototype.routeRegex = function (regex, f) {
    f._regex = regex;
    this.routes[regex] = f;
}

View.prototype.call = function (route) {
    if (this.setup) this.setup();
    return this.routes[route].apply(this, arguments);
}

var app = new App();

function getCookie(name) {
    var value = "; " + document.cookie;
    var parts = value.split("; " + name + "=");
    if (parts.length == 2) return parts.pop().split(";").shift();
}

app.openWebSocket = function () {
    if (window.location.protocol != "https:") {
        prefix = "ws://";
    } else {
        prefix = "wss://";
    }

    this.ws = new WebSocket(prefix + window.location.hostname + ":7080");

    this.ws.onopen = (function (eve) {
        this.ws.send("auth " + getCookie("s"));
    }).bind(this);

    this.ws.onmessage = (function (eve) {
        var data = JSON.parse(eve.data);
        if (this.socketEventHandlers[data.type]) {
            this.socketEventHandlers[data.type] = this.socketEventHandlers[data.type].map((function (item) {
                if (item && item.call(this, data) != false) {
                    return item;
                }
            }).bind(this));
        }

        if (data.type == "notification") {
            $.notify.apply(this, data.args);
        }

        if (data.type == "hover") {
            if (data.action == "create") {
                this.hover(data.title, data.content);
            } else if (data.action == "clear") {
                this.hoverClear();
            }
        }
    }).bind(this);

    this.ws.onclose = (function (eve) {
        console.error("WS was closed, attempting reconnect in " + this.wsDelay + " seconds...");
        setTimeout((function () {
            this.openWebSocket();
        }).bind(this), this.wsDelay * 1000);

        // Increment the retry delay
        if (this.wsDelay < 120) {
            this.wsDelay += 5
        }
    }).bind(this);
}

app.hover = (function (title, content) {
    var options = options || {};

    $(document.body).append(this.render("hover", {
        title: title,
        content: content
    }));
}).bind(app);

app.hoverClear = (function () {
    $(".hover-alert").fadeOut();
}).bind(app);

app.teardown = (function () {
    this.ws.close();
}).bind(app);

app.setup = function (userData) {
    this.wsDelay = 10;

    if (typeof(WebSocket) == "function") {
        this.openWebSocket();
    } else {
        $.notify(
            "Your browser does not support HTML5 websockets and will <b>not</b> work on this site. " +
            "Please consider upgrading to a modern version of Chrome or Firefox.", "danger");
    }

    // Tool tips oooh yeahhh
    $('[data-toggle="tooltip"]').tooltip()

    // Call this on page close
    $(window).unload(app.teardown);

    if (userData.notifications) {
        _.each(userData.notifications, function (item) {
            $.notify(item[1], item[0])
        })
    }

    if (userData.authed) {
        this.user = userData.user;

        $("[fort-user=true]").show();

        if (this.user.group === "super" || this.user.group === "admin") {
            $(".admin").show();
        }

        if (this.user.settings && !this.user.settings.trade_url) {
            $("#no-trade-url-alert").removeClass("hide");
        }
    } else {
        this.user = null;

        $("[fort-user=false]").show();
    }

    if (this.user) {
        $.get("/api/trade/pending", (function (data) {
            if (data.trade) {
                this.hover("Pending Trade Offer", data.trade);
            }
        }).bind(this));
    }

};

