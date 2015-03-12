var news = app.view("news");

news.route("/news", (function () {
    this.render_news_posts();
}).bind(news));

news.render_news_posts = (function () {
    var on_success = (function (data) {
        $(".news-container").empty();
        
        _.each(data.news_posts, (function (news_post) {
            console.log(news_post);
            $(".news-container").append(this.app.render("news_card", {
                news_post: news_post
            })).bind(this);
        }).bind(this))
    }).bind(this)
    
    $.ajax("/api/news", {
            success: on_success
    })
}).bind(news)

