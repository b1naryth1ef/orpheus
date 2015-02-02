
function paginate(data, per_page) {
    var numPages = Math.ceil(data.length / per_page),
        pages = [];

    _.range(numPages).map(function (i) {
        pages.push(data.slice(per_page * i, (per_page * i) + per_page));
    });

    return pages;
}

var InventoryView = function (app, el, settings) {
    this.app = app;
    this.el = el;
    this.settings = settings || {};

    this.page = 0;
    this.pages = 0;
}

InventoryView.prototype.parseData = function (data) {
    data.sort(function (a, b) {
        return b.price - a.price
    })

    // Now lets paginate the data
    data = paginate(data, 30);
    this.pages = data.length;

    var newData = [];
    for (page in data) {
        newData.push(paginate(data[page], 6));
    }

    return {
        "pages": newData
    }
}

InventoryView.prototype.gotoPage = function (page) {
    $(".inv-page[data-page='" + this.page +"']").hide();
    $(".inv-paginate[data-page='" + this.page + "']").parent().removeClass("active");
    this.page = page;
    $(".inv-page[data-page='" + this.page +"']").show();
    $(".inv-paginate[data-page='" + this.page + "']").parent().addClass("active");
}

InventoryView.prototype.render = function (data, opts) {
    var opts = opts || {};

    if (opts.filtered) {
        var data = _.filter(data, function (obj) {
            if (opts.filtered.indexOf(obj.uid) == -1) {
                return obj
            }
        });
    }

    $(this.el).html(this.app.render("inventory", this.parseData(data)));

    if (opts.refresh) {
        $(".inv-page[data-page='0']").fadeIn();
    } else {
        $(".inv-page[data-page='0']").show();
    }

    $(".inv-paginate").click((function (ev) {
        if ($(ev.target).hasClass("back")) {
            if (this.page > 0) {
                this.gotoPage(this.page - 1);
            }
        } else if ($(ev.target).hasClass("forward")) {
            if (this.page+1 < this.pages) {
                this.gotoPage(this.page + 1);
            }
        } else if ($(ev.target).hasClass("page")) {
            this.gotoPage(parseInt($(ev.target).attr("data-page")));
        }
    }).bind(this));
}

