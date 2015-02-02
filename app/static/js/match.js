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
            $("#bet-inventory-loader").fadeOut();
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
    $.ajax("/api/match/" + id + "/info", {
        success: (function (data) {
            this.cachedMatch = data.match;

            $(".matches-container").html(this.app.render("single_match", {
                match: data.match,
                time: moment.unix(data.match.when),
            }));
        }).bind(this)
    });
}

match.getEmptyBetSlots = function () {
    return _.filter($(".bet-slot:visible"), function (item) {
        return $(item).has("em").length;
    });
}

match.addItemToSlot = function ($item) {
    var slot = $(this.getEmptyBetSlots()[0]);
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
        } else if (this.getEmptyBetSlots().length > 0) {
            this.ignored.push(target.attr("data-uid"));
            this.inventoryView.render(this.cachedInventory, {refresh: false, filtered: this.ignored});
            this.addItemToSlot(target);
        }
    }).bind(this));

    // $(ev.target).empty().append('<em style="font-size: 9em;" class="fa fa-question"></em>');
});
