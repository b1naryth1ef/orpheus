
$(function (){
	$.get('/bettable_items', appendToList);

	function appendToList(bettable_items) {
		var list = [];
		for(var i in bettable_items){
			list.push($('<li>', { text: bettable_items[i] }));
		}
		$('.bettable_items-list').append(list);
	}
});