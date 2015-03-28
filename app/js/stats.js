var stats = app.view("stats");

// TODO add event annotations? e.g. "a major happened here"
// http://www.flotcharts.org/flot/examples/annotating/index.html
// Annotations for 'high/low' points
// marking for 'baseline' is kind of ugly
stats.renderStats = (function(id){
	var renderStatsFromData = (function(history, teams){
		var showSample = history.length < 10;

		$(".stats-container").html(this.app.render("stats_page", {showSample:showSample}));

		$("#stats-history-display").height(750);

		$(".stats-container").resizable({
			maxWidth:1000,
			maxHeight:750,
			minWidth:450,
			minHeight:100
		});
		// not enough history to give a coherent stats experience, send them over
		// to the sample stats page

		if(!history || history.length == 0){
			return;
		}

		// Stop the dropdown from disappearing when unticking/ticking options
		$('#stats-history-display-options').on('click', function(event){
			event.stopPropagation();
		});

		var teams_dict = {};

		teams_dict['all'] = stats.aggregateAll(history);

		for(var i = 0; i < teams.length; i++){
			//<li><a href="#"><input type="checkbox"><span class="lbl"> All Teams</span></a></li>
			var elem = $('<li>').append(
					$('<a>', {href:"#"})
					.append($('<input>', {type:"checkbox", id:teams[i].id, class:'options-checkbox'}))
					.append($('<span>', {class:"lbl"})
						.html('    ' + teams[i].name)
						));
			var history_values = [];
			var initialDate = [moment.utc(history[0].match_date).local().subtract(1, 'd'), 0];

			history_values.push(0);
			history_values.push(initialDate);
			teams_dict[teams[i].id] = history_values;
			$("#stats-history-display-options").append(elem);
		}

		teams_dict = stats.filterDataByTeam(teams_dict, history);

		for(var team in teams_dict){
			if(teams_dict[team].length == 2){
				$('#'+team).parent().remove();	
			}
		}
		console.log(teams_dict);
		// Generate the initial plot that the user will see, i.e. the cumulative one 
		stats.generatePlots(history, stats.itemizeSelectedPlots(teams, teams_dict));

		$('.options-checkbox').change(function(){
			stats.generatePlots(history, stats.itemizeSelectedPlots(teams, teams_dict));
		});

		$('#all-teams-checkbox').click(function(){
			stats.generatePlots(history, stats.itemizeSelectedPlots(teams, teams_dict));
		});

		$('#clear-selection').click(function(){
			$('.options-checkbox').prop('checked', false);
			$('#all-teams-checkbox').prop('checked', true);
			stats.generatePlots(history, stats.itemizeSelectedPlots(teams, teams_dict));
		});

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

	if(!id){
		$.ajax("/api/stats/value/history", {
			success: function(history){
				$.ajax("/api/team/list", {
					success: function(teams){
						renderStatsFromData(history.history, teams.teams);
					}
				})
			}
		});
	} else {
		$.ajax("/api/stats/value/history", {
			data:{
				id:id
			},
			success: function(history){
				$.ajax("/api/team/list", {
					success: function(teams){
						renderStatsFromData(history.history, teams.teams);
					}
				})
			}
		});
	}
}).bind(stats);

stats.aggregateAll = (function(history){
	history_values = [];
	history_values.push(0);
	var initialDate = [moment.utc(history[0].match_date).local().subtract(1, 'd'), 0];
	history_values.push(initialDate);
	history_values[0] += history[0].value * (history[0].won? 1 : -1);

	if(history.length == 1){
		history_values.push([moment.utc(history[0].match_date).local(), history_values[0]]);
	}

	for(var i = 1; i < history.length; i++){
		var prev = moment.utc(history[i-1].match_date).local();
		var curr = moment.utc(history[i].match_date).local();

		if(!(curr.dayOfYear() == prev.dayOfYear() && curr.year() == prev.year())){
			history_values.push([prev, history_values[0]]);
		}

		history_values[0] += history[i].value * (history[i].won? 1 : -1);

		if((i == history.length - 1 && !(curr.dayOfYear() == prev.dayOfYear() && curr.year() == prev.year()))){
			history_values.push([curr, history_values[0]]);
		}
	}

	return history_values;
}).bind(stats);

stats.filterDataByTeam = (function(map, history){
	for(var i = 0; i < history.length; i++){
		var curr = moment.utc(history[i].match_date).local();
		var histid = parseInt(history[i].team);
		map[histid][0] += history[i].value * (history[i].won? 1 : -1);

		map[histid].push([curr, map[histid][0]]);
	}
	return map;
}).bind(stats);

stats.generatePlots = (function(history, plots){
	var markings = [];
	if(history.length > 0){
		markings = [{
			yaxis:{from:1, to:-1},
	color:"#000000", 
	lineWidth:1
		}];
	}
	if(plots.length == 0){
		$.plot("#stats-history-display", [[]]);

	} else {
	$.plot("#stats-history-display", plots, {
		xaxis:{
			mode:"time",
	min: moment.utc(history[0].match_date).local().subtract(1, 'd'),
	max: moment.utc(history[history.length - 1].match_date).local().add(1, 'd'),
	minTickSize:[1, "day"]
		},
	yaxis:{
		minTickSize: [1, "dollar"]
	},
	series:{
		points:{show:true},
	lines:{show:true}
	}, 
	grid:{
		markings:markings
	}
	});
	}
}).bind(stats);

stats.aggregateChecked = (function(){
	if($('#all-teams-checkbox').attr('checked') == true){
		return [];
	} else {
		var selections = [];
		$('.options-checkbox').each(function(){
			if(this.checked){
				selections.push(parseInt(this.id));
			}
		});
		return selections;
	}
}).bind(stats);

stats.itemizeSelectedPlots = (function(teams, teams_dict){
	var plots = [];
	var selected = stats.aggregateChecked();

	plots.push();

	if($('#all-teams-checkbox').prop('checked')){
		plots.push({label:"Aggregate", data:teams_dict['all']});
	}

	for(var i = 0; i < teams.length; i++){
		if(selected.indexOf(teams[i].id) != -1){
			plots.push({label:teams[i].name, data:teams_dict[teams[i].id]});
		}
	}

	return plots;
}).bind(stats);

stats.route("/stats", (function () {
	this.renderStats();
}).bind(stats));

stats.route("/stats/sample", (function () {
	this.renderStats(1);
}).bind(stats));

