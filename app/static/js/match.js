var match = app.view("match");

match.inventoryReadyEvent = function (data) {
    clearTimeout(this.waitingForInventory);

    if ($("#bet-modal").data("bs.modal").isShown) {
        console.log("would do stuff here");
    }
    return false;
}

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

match.routeRegex(/^\/match\/(\d+)$/, function (route, id) {
    this.renderSingleMatch(id);

    $(".matches-container").delegate("#bet-btn", "click", (function (ev) {
        if (!this.cachedMatch) { return; }

        $(".bet-modal-container").html(this.app.render("bet_modal", {
            match: this.cachedMatch
        }));

        this.queueInventoryLoad();
        $("#bet-modal").modal("show");

    }).bind(this));
});
