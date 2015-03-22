var news = app.view("news");

news.route("/news", (function () {
    this.renderNewsPosts();
}).bind(news));

news.renderNewsPosts = (function () {
    $.ajax("/api/news/list", {
        success: (function (data) {
            $(".news-container").empty();

            _.each(data.posts, (function (post) {
                $(".news-container").append(this.app.render("news_post", {
                    news_post: post
                })).bind(this);
            }).bind(this))
        }).bind(this)
    });
}).bind(news)

