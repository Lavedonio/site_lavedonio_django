function zoom() {
	console.log(window.innerWidth);
	if(window.innerWidth < 350) {
		document.body.style.zoom = 0.9;
	}
	else {
		document.body.style.zoom = 1;
	}
}


window.onload = function() {
	zoom();

	window.addEventListener('resize', function(event) {
		console.log(window.innerWidth);
		if(window.innerWidth < 350) {
			document.body.style.zoom = "90%";
		}
		else {
			document.body.style.zoom = "100%";
		}
	});
};