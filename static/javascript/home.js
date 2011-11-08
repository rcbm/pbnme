var time;
var timer_is_on=0;
words = ['posse', 'circle', 'group', 'crew', 'gang'];

function timedReplace() {
    word = words.shift();
    document.getElementById('group').innerHTML=word;
    words.push(word);
    time = setTimeout("timedReplace()",5000);
}
    
function doTimer(){
    if (!timer_is_on) {
	timer_is_on=1;
	timedReplace();
    }
}
