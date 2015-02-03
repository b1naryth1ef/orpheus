var match = app.view("match");

match.inventoryReadyEvent = (function (data) {
    clearTimeout(this.waitingForInventory);

    if ($("#bet-modal").data("bs.modal").isShown) {
        this.cachedInventory = data.inventory;
        this.inventoryView.render(data.inventory);
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

            $(".matches-container").html(this.app.render("single_match", {
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

match.routeRegex(/^\/match\/(\d+)$/, function (route, id) {
    this.renderSingleMatch(id);
    this.inventoryView = new InventoryView(this.app, "#bet-inventory");
    this.cachedInventory = null;
    this.ignored = [];

    $(".matches-container").delegate("#bet-btn", "click", (function (ev) {
        if (!this.cachedMatch) { return; }

        $(".bet-modal-container").html(this.app.render("bet_modal", {
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
            this.ignored = _.without(this.ignored, target.attr("data-uid"));
            this.inventoryView.render(this.cachedInventory, {refresh: false, filtered: this.ignored});
        } else if (this.getBetSlots(true).length > 0) {
            this.ignored.push(target.attr("data-uid"));
            this.inventoryView.render(this.cachedInventory, {refresh: false, filtered: this.ignored});
            this.addItemToSlot(target);
        }
    }).bind(this));

    $(".matches-container").delegate(".btn-placebet", "click", (function (ev) {
        var team = $(ev.target).closest("button").attr("data-team");

        var items = _.map(this.getBetSlots(), function (item) {
            console.log(item);
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
                    // TODO: error alert
                    console.error(data.message);
                } else {
                    // TODO: success alert
                    $("#bet-modal").modal("hide");
                    this.renderSingleMatch(this.cachedMatch.id);
                }
            }).bind(this)
        });
    }).bind(this));
});
