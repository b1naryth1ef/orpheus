var match = app.view("match");

match.inventoryReadyEvent = (function (data) {
    clearTimeout(this.waitingForInventory);

    if ($("#bet-modal").data("bs.modal").isShown) {
        this.inventoryView.updateData(data.inventory);
        this.inventoryView.render();
    }
    return false;
}).bind(match);

match.queueInventoryLoad = function () {
    app.waitForEvent("inventory", this.inventoryReadyEvent);

    if (this.waitingForInventory) {
        clearTimeout(this.waitingForInventory);
    }

    this.waitingForInventory = setTimeout((function () {
        if ($("#bet-inventory-loader").length) {
            $("#bet-inventory-load-failed").fadeIn();
        }
    }).bind(this), 10000);

    $.ajax("/api/user/inventory", {
        success: (function (data) {
            if (!data.success) {
                // TODO: error :)
                console.error("Failed to load inventory!");
                return;
            }
        }).bind(this)
    });
}

match.renderSingleMatch = function (id) {
    $(".matches-container").addClass("whirl");

    $.ajax("/api/match/" + id + "/info", {
        success: (function (data) {
            this.cachedMatch = data.match;

            $(".matches-container").html(this.app.render("match_page", {
                match: data.match,
                time: moment.unix(data.match.when),
            })).removeClass("whirl");

            $('[data-toggle="tooltip"]').tooltip({
                html: true,
                container: 'body'
            });
        }).bind(this)
    });
}

match.getBetSlots = function (empty) {
    return _.filter($(".bet-slot:visible"), function (item) {
        var isEmptySlot = $(item).has("em").length;

        if (empty) return isEmptySlot
        else return !isEmptySlot
    });
}


match.addItemToSlot = function ($item) {
    var slot = $(this.getBetSlots(true)[0]);
    slot.closest(".row").prepend($item);
    slot.hide();
    $item.addClass("bet-slot").addClass("col-centered");
}

match.refreshFromSocket = function (data) {
    if (data.id == this.cachedMatch.id) {
        this.renderSingleMatch(id);
    }
}

match.routeRegex(/^\/match\/(\d+)$/, function (route, id) {
    app.waitForEvent("refresh-match", this.refreshFromSocket);
    this.renderSingleMatch(id);
    this.inventoryView = new InventoryView(this.app, "#bet-inventory");
    this.ignored = [];

    $(".matches-container").delegate("#bet-btn", "click", (function (ev) {
        if (!this.cachedMatch) { return; }

        $(".bet-modal-container").html(this.app.render("match_bet_modal", {
            match: this.cachedMatch
        }));

        this.queueInventoryLoad();
        $("#bet-modal").modal("show");

    }).bind(this));

    $(".matches-container").delegate(".inventory-item", "click", (function (ev) {
        var target = $($(ev.target).closest(".inventory-item"));

        if (target.hasClass("bet-slot")) {
            target.detach();
            $(".bet-slot:hidden").first().show();
            this.inventoryView.filtered = _.without(
                    this.inventoryView.filtered, target.attr("data-id"));
            this.inventoryView.render({refresh: true});
        } else if (this.getBetSlots(true).length > 0) {
            this.inventoryView.filtered.push(target.attr("data-id"));
            this.inventoryView.render({refresh: true});
            this.addItemToSlot(target);
        }
    }).bind(this));

    // TODO: make a seperate function
    $(".matches-container").delegate(".btn-placebet", "click", (function (ev) {
        if (app.user && app.user.token == null) {
            $("#bet-modal").modal("hide");
            $.notify("Error: You must setup your trade URL before betting." +
                "Please <a href=\"/settings\">setup a trade URL</a> now!", "danger")
            return
        }

        var team = $(ev.target).closest("button").attr("data-team");

        var items = _.map(this.getBetSlots(), function (item) {
            return $(item).attr("data-id");
        });

        $.ajax("/api/match/" + this.cachedMatch.id + "/bet", {
            type: "POST",
            data: {
                team: team,
                items: JSON.stringify(items)
            },
            success: (function (data) {
                if (!data.success) {
                    $("#bet-modal").modal("hide");
                    $.notify("Error placing bet: " + data.message, "danger");
                } else {
                    $("#bet-modal").modal("hide");
                    $.notify("Placed Bet!", "success");
                    this.renderSingleMatch(this.cachedMatch.id);
                }
            }).bind(this)
        });
    }).bind(this));

    // TODO: this should probably also be a seperate function
    $(".matches-container").delegate(".btn-switchteam", "click", (function (ev) {
        $.ajax("/api/match/" + this.cachedMatch.id + "/switchteam", {
            type: "POST",
            data: { },
            success: (function (data) {
                if (!data.success) {
                    $.notify("Unable to Switch Team: " + data.message, "danger");
                } else {
                    $.notify("Team Switched!", "success");
                    this.renderSingleMatch(this.cachedMatch.id);
                }
            }).bind(this)
        });
    }).bind(this));
});
