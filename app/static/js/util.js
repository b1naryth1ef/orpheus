
var InventoryView = function (app, el, settings) {
    this.app = app;
    this.el = el;
    this.settings = settings || {};
}

InventoryView.prototype.parseData = function (data) {
    data.sort(function (a, b) {
        return b.price - a.price
    })

    var rows = [], row = [];

    for (index in data) {
        row.push(data[index]);

        if (row.length == 6) {
            rows.push(row);
            row = [];
        }
    }

    if (row.length) {
        rows.push(row);
    }

    return {
        "rows": rows
    }
}

InventoryView.prototype.render = function (data) {
    console.log(data);
    console.log(this.parseData(data));
    $(this.el).html(this.app.render("inventory", this.parseData(data)));
}

