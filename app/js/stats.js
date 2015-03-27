var stats = app.view("stats");

stats.renderStats = function(){
	var renderStatsFromData = (function(data){
		$(".stats-container").html(this.app.render("stats_page", {}));
		var history_data = [];
		var cumulative = 0;
		for(var i = 0; i < data.history.length; i++){
			history_data.push([i, cumulative]);
			cumulative += data.history[i].value * (data.history[i].won? 1 : -1);
		}
		//$("#stats-history-display").width(1000);

		$("#stats-history-display").height(750);
		$(".stats-container").resizable({
			maxWidth:1000,
			maxHeight:750,
			minWidth:450,
			minHeight:100
		});
		$.plot("#stats-history-display", [history_data]);

		$("#value-history").click((function(){
			console.log("value-history");
		}).bind(this));
		$("#bet-win-loss").click((function(){
			console.log("bet-win-loss");
		}).bind(this));
		$("#help").click((function(){
			console.log("help");
		}).bind(this));

	}).bind(this);

	$.ajax("/api/stats/value/history", {
		success: renderStatsFromData
	});
}

stats.route("/stats", function () {
	this.renderStats();
});

