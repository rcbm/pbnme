/*
  <a href="" class="hideFresh" onclick="removeEntry({{ forloop.parentloop.counter }}, $(this), '{{ e.0 }}', '{{ e.1 }}');"></a>

  function removfeeeeeeeeeEntry(num, div, q, p) {
    $.ajax({url: '/removeEntry?q=' + q + '&p=' + p,context: document.body,type: 'POST'});
    counterObj = $('.counter-'+num);
    count = counterObj.html() - 1;
    counterObj.html(count);
    
    if (count < 1) {
	div.parent().fadeOut();
	$('.fresh-counter-' + num).fadeOut(function(){
		div.parent().parent().append(no_results);
	    });
    } else {
	div.parent().fadeOut();
    }
}
*/
function purgeEvent(num, div, eventKey) {
    $.ajax({url: '/purge?key=' + eventKey, context: document.body, type: 'POST'});
    // This goes looking for the counter and decrements it
    /*counterObj = $('.counter-'+num);
    count = counterObj.html() - 1;
    counterObj.html(count);
    */
    // This checks to see if the counter is at zero
    // If so it inserts a placeholder div
    //
    /*
    if (count < 1) {
	div.parent().fadeOut();
	$('.fresh-counter-' + num).fadeOut(function(){
		div.parent().parent().append(no_results);
	    });
    } else {
	div.parent().fadeOut();
    }
    */
    div.parent().parent().fadeOut();
}
