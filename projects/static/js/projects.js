// Solution based on StackOverflow answer https://stackoverflow.com/a/4770179/11981524
var lock = document.getElementById('lockpage');
var close = document.getElementById('closeicon');

var lockframe = document.getElementById('lockframe');
var backgroundfill = document.getElementById('backgroundfill');

var locked = false;
var page_ypos;

// left: 37, up: 38, right: 39, down: 40,
// spacebar: 32, pageup: 33, pagedown: 34, end: 35, home: 36
var keys = {32: 1, 33: 1, 34: 1, 35: 1, 36: 1, 37: 1, 38: 1, 39: 1, 40: 1};

function preventDefault(e) {
	e.preventDefault();
}

function preventDefaultForScrollKeys(e) {
	if(keys[e.keyCode]) {
		preventDefault(e);
		return false;
	}
}

// modern Chrome requires { passive: false } when adding event
var supportsPassive = false;
try {
	window.addEventListener("test", null, Object.defineProperty({}, 'passive', {
		get: function () { supportsPassive = true; } 
	}));
} catch(e) {}

var wheelOpt = supportsPassive ? { passive: false } : false;
var wheelEvent = 'onwheel' in document.createElement('div') ? 'wheel' : 'mousewheel';

// call this to Disable
function disableScroll() {
	page_ypos = document.documentElement.scrollTop || window.pageYOffset;

	window.addEventListener('DOMMouseScroll', preventDefault, false); // older FF
	window.addEventListener(wheelEvent, preventDefault, wheelOpt); // modern desktop
	window.addEventListener('touchmove', preventDefault, wheelOpt); // mobile
	window.addEventListener('keydown', preventDefaultForScrollKeys, false);

	// Page elements
	lockframe.classList.add("fullscreen");
	backgroundfill.classList.add("fill-background");
	close.classList.remove("d-none");
}

// call this to Enable
function enableScroll() {
	window.scrollTo(0, page_ypos);

	window.removeEventListener('DOMMouseScroll', preventDefault, false);
	window.removeEventListener(wheelEvent, preventDefault, wheelOpt); 
	window.removeEventListener('touchmove', preventDefault, wheelOpt);
	window.removeEventListener('keydown', preventDefaultForScrollKeys, false);

	// Page elements
	lockframe.classList.remove("fullscreen");
	backgroundfill.classList.remove("fill-background");
	close.classList.add("d-none");
}

function isTouchScreen() {
	return window.matchMedia('(hover: none)').matches;
}


// Event listeners
lock.addEventListener("click", function(event) {
	if(locked) {
		locked = !locked;
		enableScroll();
	}
	else {
		locked = !locked;
		disableScroll();
	}
});

close.addEventListener("click", function(event) {
	if(locked) {
		locked = !locked;
		enableScroll();
	}
});
