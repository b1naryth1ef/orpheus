var stats = app.view("stats");

stats.renderStats = function(){
	var renderStatsFromData = (function(data){
		$(".stats-container").html(this.app.render("stats_page", {}));
		$(function(){
			var history_data = [];
			var cumulative = 0;
			for(var i = 0; i < data.history.length; i++){
				history_data.push([i, cumulative]);
				cumulative += data.history[i].value * (data.history[i].won? 1 : -1);
				console.log(data.history[i].match_date);
			}

			$.plot("#stats-history-display", [history_data]);
		});     

	}).bind(this);

	$.ajax("/api/stats/value/history", {
		success: renderStatsFromData
	});
}

stats.route("/stats", function () {
	this.renderStats();
});

