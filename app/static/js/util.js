
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
        "pages": newData,
        "cur_page": this.page
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

    // This is used for when we "select" inventory items
    if (opts.filtered) {
        var data = _.filter(data, function (obj) {
            if (opts.filtered.indexOf(obj.id) == -1) {
                return obj
            }
        });
    }

    $(this.el).html(this.app.render("inventory", this.parseData(data)));

    // If we're refreshing, we want to just immediatly update things.
    //  fading would be too jolty.
    if (opts.refresh) {
        $(".inv-page[data-page='" + this.page + "']").show();
    } else {
        $(".inv-page[data-page='" + this.page + "']").fadeIn();
    }

    // Bind pagination events (TODO: delegate)
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

function getDataFromField(field) {
    var field = $(field);

    switch (field.get(0).tagName) {
        case "SELECT":
            return field.val();
        case "INPUT":
            if (field.is(":checkbox")) {
                return field.is(":checked");
            }
            return field.val();
        case "DIV":
            if (field.hasClass("date-field")) {
                return field.data('date') ? moment(field.data('date')).format('X') : null;
            }
            break;
        default:
            break;
    }
}

function setupDateFields() {
    _.each($(".date-field"), function (el) {
        var defDate = undefined;

        if ($(el).attr("data-default")) {
            defDate = moment(parseInt($(el).attr("data-default")) * 1000);
        }

        $(el).datetimepicker({
            defaultDate: defDate
        })
    })
}

