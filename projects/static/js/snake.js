var canvas;
var canvasContext;
var BLOCK_WIDTH;
var BLOCK_HEIGHT;
var NUMBER_OF_TILES = 40;
var REFRESH_RATE = 50;

var player_lost = false;
var game_started = false;
var game_ended = false;

// -------------- Global functions --------------

function reset_game(player, food) {
	player.reset();
	food.new_rand_location(player);
	player_lost = false;
	game_ended = false;
}

function handleMouseClick(event, player, food) {
	if(!game_started) {
		game_started = true;
	}
	if(game_ended) {
		reset_game(player, food);
	}
}

// ------------- /Global functions --------------

// -------------------- Main --------------------

window.onload = function() {
	// window.onload: executes function after loading entire page

	canvas = document.getElementById('gameCanvas');
	canvasContext = canvas.getContext('2d');

	var rfr_selector = document.getElementById('refresh-rate');
	var ntl_selector = document.getElementById('num-of-tiles');

	NUMBER_OF_TILES = Number(ntl_selector[ntl_selector.selectedIndex].value);
	REFRESH_RATE = Number(rfr_selector[rfr_selector.selectedIndex].value);

	BLOCK_WIDTH = canvas.width / NUMBER_OF_TILES;
	BLOCK_HEIGHT = canvas.height / NUMBER_OF_TILES;

	var player = new Snake(Math.floor(NUMBER_OF_TILES / 2), Math.floor(NUMBER_OF_TILES / 2));
	var food = new Food();

	var program_timer = setInterval(function() {
		moveEverything(player, food);
		drawEverything(player, food);
	}, REFRESH_RATE);

	// .addEventListener method (http://www.w3schools.com/jsref/met_element_addeventlistener.asp)
	// Event types: http://www.w3schools.com/jsref/dom_obj_event.asp
	document.addEventListener('keydown', function(event) {
		// space and arrow keys
		if([32, 37, 38, 39, 40].indexOf(event.keyCode) > -1) {
			event.preventDefault();
		}
		// const keyName = event.keyCode;
		// console.log('keydown event \n\n' + 'chave:' + keyName);
		player.update_direction(event.keyCode);
	});

	canvas.addEventListener('mousedown', function(event) {
		handleMouseClick(event, player, food);
	});

	ntl_selector.addEventListener('change', function(event) {
		NUMBER_OF_TILES = Number(ntl_selector[ntl_selector.selectedIndex].value);
		BLOCK_WIDTH = canvas.width / NUMBER_OF_TILES;
		BLOCK_HEIGHT = canvas.height / NUMBER_OF_TILES;
		game_started = false;
		reset_game(player, food);
	});

	rfr_selector.addEventListener('change', function(event) {
		clearInterval(program_timer);

		REFRESH_RATE = Number(rfr_selector[rfr_selector.selectedIndex].value);
		game_started = false;
		reset_game(player, food);

		program_timer = setInterval(function() {
			moveEverything(player, food);
			drawEverything(player, food);
		}, REFRESH_RATE);
	});


	// Change direction by button click
	document.getElementById("up-arrow").addEventListener('click', function(event) {
		player.update_direction(38);
	});
	document.getElementById("left-arrow").addEventListener('click', function(event) {
		player.update_direction(37);
	});
	document.getElementById("down-arrow").addEventListener('click', function(event) {
		player.update_direction(40);
	});
	document.getElementById("right-arrow").addEventListener('click', function(event) {
		player.update_direction(39);
	});
}

// ------------------- /Main -------------------

// ---------------- Constructors ----------------

function Snake(x, y) {
	this.x = x;
	this.y = y;
	this.x_speed = 1;
	this.y_speed = 0;
	this.direction = 0; // 0 = right; 1 = up; 2 = left; 3 = down
	this.score = 0;
	this.hi_score = 0;
	this.body = [[x, y], [x - 1, y], [x - 2, y]];

	this.update_position = function(food) {
		this.x += this.x_speed;
		this.y += this.y_speed;

		var food_eaten = true;
		if(food.is_not_eaten(this.x, this.y)) {
			this.body.pop();
			food_eaten = false;
		}
		this.body.unshift([this.x, this.y]);

		return food_eaten;
	}

	this.update_direction = function(key) {
		switch(key) {
			case 39:  // Arrow Right
				if(this.direction !== 0 && this.direction !== 2) {
					this.direction = 0;
				}
				break;
			case 37:  // Arrow Left
				if(this.direction !== 0 && this.direction !== 2) {
					this.direction = 2;
				}
				break;
			case 38:  // Arrow Up
				if(this.direction !== 1 && this.direction !== 3) {
					this.direction = 3;
				}
				break;
			case 40:  // Arrow Down
				if(this.direction !== 1 && this.direction !== 3) {
					this.direction = 1;
				}
				break;
			default:
				break;
		}
		this.update_speed();
	}

	this.update_speed = function() {
		this.y_speed = Math.round(Math.sin(this.direction * Math.PI / 2));
		this.x_speed = Math.round(Math.cos(this.direction * Math.PI / 2));
	}

	this.reset = function() {
		this.x = Math.floor(NUMBER_OF_TILES / 2);
		this.y = Math.floor(NUMBER_OF_TILES / 2);
		this.x_speed = 1;
		this.y_speed = 0;
		this.direction = 0;
		this.body = [[this.x, this.y], [this.x - 1, this.y], [this.x - 2, this.y]];
		this.score = 0;
	}

	this.died = function() {
		var died = false;

		// Player is off canvas
		if((this.x - 1) * (this.y - 1) < 0 || this.x > NUMBER_OF_TILES || this.y > NUMBER_OF_TILES) {
			died = true;
		}

		// Check if player has crossed itself
		var aux_array = [];
		for (var i = 0; i < this.body.length; i++) {
			for (var j = 0; j < aux_array.length; j++) {
				if(Math.round(aux_array[j][0]) === Math.round(this.body[i][0]) && Math.round(aux_array[j][1]) === Math.round(this.body[i][1])) {
					died = true;
				}
			}
			aux_array.push(this.body[i]);
		}

		return died;
	}

	this.not_occupied_positions = function() {
		var x;
		var y;

		var available_positions = [];

		for(var i = 1; i <= Math.pow(NUMBER_OF_TILES, 2); i++) {
			available_positions.push(i);
		}

		for (i = 0; i < this.body.length; i++) {
			x = Math.round(this.body[i][0]);
			y = Math.round(this.body[i][1]);

			available_positions.splice(y * NUMBER_OF_TILES + x, 1);
		}

		return available_positions;
	}

	this.draw = function() {
		for(var i = 0; i < this.body.length; i++) {
			var x = this.body[i][0];
			var y = this.body[i][1];
			colorRect((x - 1) * BLOCK_WIDTH, (y - 1) * BLOCK_HEIGHT, BLOCK_WIDTH, BLOCK_HEIGHT, 'green');
		}
	}

	this.log = function() {
		console.log("\nPlayer status");
		console.log("Head position:");
		console.log("x: " + this.x);
		console.log("y: " + this.y);
		switch(this.direction) {
			case 0:
				console.log("Direction: Right (" + this.direction + ")");
				break;
			case 1:
				console.log("Direction: Up (" + this.direction + ")");
				break;
			case 2:
				console.log("Direction: Left (" + this.direction + ")");
				break;
			case 3:
				console.log("Direction: Down (" + this.direction + ")");
				break;
			default:
				console.log("Direction: Error - Invalid (" + this.direction + ")");
				break;
		}
		console.log("Lenght: " + this.body.length);
	}
}

function Food() {
	this.x = 23;
	this.y = 20;

	this.new_rand_location = function(player) {
		available_positions = player.not_occupied_positions();

		var new_position = available_positions[getRandomInt(0, available_positions.length)];

		this.y = Math.floor(new_position / NUMBER_OF_TILES) + 1;
		this.x = new_position - ((this.y - 1) * NUMBER_OF_TILES) + 1;
	}

	this.is_not_eaten = function(x, y) {
		// Check if both positions are equal
		return !(this.x === x && this.y === y);
	}

	this.draw = function(color = 'red') {
		colorRect((this.x - 1) * BLOCK_WIDTH, (this.y - 1) * BLOCK_HEIGHT, BLOCK_WIDTH, BLOCK_HEIGHT, color);
	}

	this.log = function() {
		console.log("\nFood status");
		console.log("Position:");
		console.log("x: " + this.x);
		console.log("y: " + this.y);
	}
}

// ------------- /Constructors -------------

function moveEverything(player, food) {
	if(game_started && !game_ended) {
		var food_eaten = player.update_position(food);

		// Check if player died
		if(player.died()) {
			player_lost = true;
			game_ended = true;
			return;
		}

		// Check the rare case of player winning the game
		if(player.body.lenght === Math.pow(NUMBER_OF_TILES, 2)) {
			player_lost = false;
			game_ended = true;
			return;
		}

		if(food_eaten) {
			food.new_rand_location(player);
			player.score++;
			if(player.hi_score < player.score) {
				player.hi_score++;
			}
		}
		player.log();
		food.log();
	}
}

function drawEverything(player, food) {
	// next line blanks out the screen with black
	colorRect(0, 0, canvas.width, canvas.height, 'black');

	if(game_started) {
		canvasContext.font = "20px Helvetica";

		// this draws the snake
		player.draw();

		// player score
		canvasContext.fillStyle = 'white';
		canvasContext.fillText("Hi-score: " + player.hi_score, 5, 20);
		canvasContext.fillText("Score: " + player.score, 5, 40);

		// next line draws the food (only case that doesnt is if player occupy all game area i.e. player won)
		if(!(game_ended && !player_lost)) {
			food.draw();
		}

		if(game_ended) {
			win_text = "Você ganhou!!";
			lose_text = "Você perdeu =(";

			canvasContext.fillStyle = 'white';

			if(player_lost) {
				canvasContext.fillText(lose_text, (canvas.width - 10 * lose_text.length) / 2, canvas.height / 3);
			} else {
				canvasContext.fillText(win_text, (canvas.width - 10 * win_text.length) / 2, canvas.height / 3);
			}

			canvasContext.fillText("clique para reiniciar", (canvas.width / 2) - 90, 5 * canvas.height / 6);
		}
	}
	else {
		canvasContext.fillStyle = 'white';
		canvasContext.font = "40px Helvetica";
		canvasContext.fillText("Snake", (canvas.width - 120) / 2, canvas.height / 3);

		canvasContext.font = "20px Helvetica";
		canvasContext.fillText("clique para começar", (canvas.width / 2) - 90, 5 * canvas.height / 6);
	}
}


// ---------- Funções auxiliares ----------

function getRandomInt(min, max) {
	// https://developer.mozilla.org/pt-BR/docs/Web/JavaScript/Reference/Global_Objects/Math/random
	min = Math.ceil(min);
	max = Math.floor(max);
	return Math.floor(Math.random() * (max - min)) + min;
}

function colorRect(leftX, topX, width, height, drawColor) {
	// Método .fillRect(a, b, c, d):
	//		a. [posição x do canto do quadrado],
	// 		b. [posição y do canto do quadrado],
	//		c. [largura do quadrado],
	//		d. [altura do quadrado]
	// Obs.: levar em consideração ao centralizar um objeto

	canvasContext.fillStyle = drawColor;
	canvasContext.fillRect(leftX, topX, width, height);
}
