var canvas;
var canvasContext;
var controls;
var baseTextSize = "32px";

const SETTINGS_HEIGHT = 150;
const CANVAS_HEIGHT_PADDING = 70;
const DEFAULT_WALL_OFFSET = 20;

const DEFAULT_WIDTH = 800;
const DEFAULT_HEIGHT = 600;

var CURRENT_PADDLE_HEIGHT = 100;

// ------------- Cursor Handling Functions -------------

function calculateMousePos(evt) {
	var rect = canvas.getBoundingClientRect(); // retorna o tamanho e a posição em relação ao canvas dentro da janela visível ao usuário da página (não em relação ao documento HTML como um todo)
	var root = document.documentElement;

	//considera as posições X e Y relativas e não totais, desconsiderando o scroll e os outros elementos da página (texto, parágrafos, divs...)
	var mouseX = evt.clientX - rect.left; // - root.scrollLeft;
	var mouseY = evt.clientY - rect.top; // - root.scrollTop;

	return {
		x:mouseX,
		y:mouseY
	};
}

function calculateTouchPos(evt) {
	var rect = canvas.getBoundingClientRect();
	var root = document.documentElement;

	var e = (typeof evt.originalEvent === 'undefined') ? evt : evt.originalEvent;
	// Idea from StackOverflow: https://stackoverflow.com/a/41993300/11981524
	var touch = e.touches[0] || e.changedTouches[0];

	
	var touchX = touch.pageX - rect.left;
	var touchY = touch.pageY - rect.top;

	return {
		x:touchX,
		y:touchY
	};
}

function handleMouseClick(evt, player1, computer, game_settings) {
	if(!game_settings.game_started) {
		game_settings.game_started = true;
	}

	if(game_settings.showingWinScreen) {
		player1.score = 0;
		computer.score = 0;
		game_settings.showingWinScreen = false;
	}
}

// ------------- /Cursor Handling Functions -------------

// -------------- Global functions --------------

function displaySettings(reload, reset, game_settings, ball=null, player1=null, computer=null) {
	var deviceHeight = document.documentElement.clientHeight;
	var deviceWidth = document.documentElement.clientWidth;

	var available_height = deviceHeight - SETTINGS_HEIGHT - CANVAS_HEIGHT_PADDING;

	if(deviceWidth < 350) {
		if(available_height < deviceWidth - 50 && (4 * available_height) / 3 < deviceWidth - 50) {
			canvas.height = available_height;
			canvas.width = (4 * canvas.height) / 3;
		}
		else {
			canvas.width = deviceWidth - 50;
			canvas.height = 0.75 * canvas.width;
		}

		controls.style.width = (canvas.width).toString() + "px";
		baseTextSize = "20px";
	}
	else if(deviceWidth < 575) {
		if(available_height < deviceWidth - 50 && (4 * available_height) / 3 < deviceWidth - 50) {
			canvas.height = available_height;
			canvas.width = (4 * canvas.height) / 3;
		}
		else {
			canvas.width = deviceWidth - 50;
			canvas.height = 0.75 * canvas.width;
		}

		controls.style.width = (canvas.width).toString() + "px";
		baseTextSize = "24px";
	}
	else if(deviceWidth < 650) {
		if(available_height < 0.8 * deviceWidth && (4 * available_height) / 3 < 0.8 * deviceWidth) {
			canvas.height = available_height;
			canvas.width = (4 * canvas.height) / 3;
		}
		else {
			canvas.width = 0.8 * deviceWidth;
			canvas.height = 0.75 * canvas.width;
		}

		controls.style.width = (canvas.width).toString() + "px";
		baseTextSize = "32px";
	}
	else if(deviceWidth < 767) {
		if(available_height < 0.7 * deviceWidth && (4 * available_height) / 3 < 0.7 * deviceWidth) {
			canvas.height = available_height;
			canvas.width = (4 * canvas.height) / 3;
		}
		else {
			canvas.width = 0.7 * deviceWidth;
			canvas.height = 0.75 * canvas.width;
		}
		canvas.width = 0.7 * deviceWidth;
		canvas.height = 0.75 * canvas.width;

		controls.style.width = (canvas.width).toString() + "px";
		baseTextSize = "32px";
	}
	else if(deviceWidth < 990) {
		if(available_height < 0.6 * deviceWidth && (4 * available_height) / 3 < 0.6 * deviceWidth) {
			canvas.height = available_height;
			canvas.width = (4 * canvas.height) / 3;
		}
		else {
			canvas.width = 0.6 * deviceWidth;
			canvas.height = 0.75 * canvas.width;
		}

		controls.style.width = (canvas.width).toString() + "px";
		baseTextSize = "32px";
	}
	else {
		if(available_height < DEFAULT_HEIGHT) {
			canvas.height = available_height;
			canvas.width = (4 * canvas.height) / 3;
		}
		else {
			canvas.width = DEFAULT_WIDTH;
			canvas.height = DEFAULT_HEIGHT;
		}

		controls.style.width = (canvas.width).toString() + "px";
		baseTextSize = "32px";
	}

	if(reload) {
		player1.resize();
		computer.resize();
		ball.resize(canvas.width / 60, game_settings.ball_speed());

		game_settings.game_started = false;

		if(reset) {
			game_settings.reset(ball, player1, computer);
		}
	}
}

// ------------- /Global functions --------------

// -------------------- Main --------------------

window.onload = function() {
	// window.onload associado a função: carrega o que tiver dentro apenas depois que a página terminar de carregar
	canvas = document.getElementById('gameCanvas'); //associa a variável canvas ao elemento no HTML
	canvasContext = canvas.getContext('2d');
	controls = document.getElementById('controls');

	// Getting ajusted canvas properties
	displaySettings(false, false, null);

	var framesPerSecond = 60;
	var game_settings = new GameSettings();
	var ball = new Ball(game_settings.ball_speed());
	var player1 = new Player('person');
	var computer = new Player('computer');

	displaySettings(true, false, game_settings, ball, player1, computer);

	// Difficulty selection
	var difficulty_selector = document.getElementById('difficulty');
	game_settings.set_difficulty(difficulty_selector[difficulty_selector.selectedIndex].value, computer);

	// Score selection
	var score_selector = document.getElementById('max-score');
	game_settings.winning_score = Number(score_selector[score_selector.selectedIndex].value);
	game_settings.check_if_disable_endgame();

	setInterval(function() {
		moveEverything(ball, player1, computer, game_settings);
		drawEverything(ball, player1, computer, game_settings);
	}, 1000/framesPerSecond);

	// Método .addEventListener (http://www.w3schools.com/jsref/met_element_addeventlistener.asp)
	canvas.addEventListener('mousemove', // http://www.w3schools.com/jsref/dom_obj_event.asp
		function(evt) {
			var mousePos = calculateMousePos(evt);
			player1.manual_move(mousePos);
		});

	canvas.addEventListener('touchmove', // http://www.w3schools.com/jsref/dom_obj_event.asp
		function(evt) {
			var touchPos = calculateTouchPos(evt);
			player1.manual_move(touchPos);
		});

	canvas.addEventListener('mousedown', function(evt) {
		handleMouseClick(evt, player1, computer, game_settings);
	});

	window.addEventListener("resize", function(event) {
		displaySettings(true, true, game_settings, ball, player1, computer);

		// Makes sure the correct computer paddle height is enabled
		game_settings.set_difficulty(difficulty_selector[difficulty_selector.selectedIndex].value, computer);
	});

	difficulty_selector.addEventListener('change', function(event) {
		game_settings.set_difficulty(difficulty_selector[difficulty_selector.selectedIndex].value, computer);

		// When difficulty level is changed, game is reseted
		game_settings.reset(ball, player1, computer);
	});

	score_selector.addEventListener('change', function(event) {
		game_settings.winning_score = Number(score_selector[score_selector.selectedIndex].value);
		game_settings.check_if_disable_endgame();
	});
}

// ------------------- /Main -------------------

// ---------------- Construtores ----------------

function Ball(base_speed) {
	this.x = 110;
	this.y = 50;
	this.default_x_speed = base_speed;
	this.x_speed = base_speed;
	this.y_speed = 2;
	this.size = 10;

	this.scored = function() {
		return (this.x < 0 || this.x + this.size > canvas.width);
	}

	this.check_if_hit_paddle = function(paddle) {
		var ball_right_bound = this.x < (paddle.x + paddle.thickness);
		var ball_left_bound = paddle.x < (this.x + this.size);
		var ball_top_bound = (this.y + this.size) > paddle.y;
		var ball_lower_bound = this.y < (paddle.y + paddle.height);

		return ball_left_bound && ball_right_bound && ball_top_bound && ball_lower_bound;
	}

	this.handle_paddle_interaction = function(player) {
		if(this.check_if_hit_paddle(player.paddle)) {
			this.x_speed = -this.x_speed;

			var deltaY = this.y - (player.paddle.y + (player.paddle.height / 2));
			this.y_speed = deltaY * 0.2;
		}
	}

	this.update = function() {
		this.x += this.x_speed;
		this.y += this.y_speed;

		if(this.y + this.size > canvas.height || this.y < 0) {
			this.y_speed = -this.y_speed;
		}

		if(this.x_speed > 0) {
			this.x_speed += 0.005;
		}
		else {
			this.x_speed -= 0.005;
		}

		// if(this.x > canvas.width || this.x < 0) {
		// 	this.x_speed = -this.x_speed;
		// }
	}

	this.resize = function(new_size, new_base_speed) {
		this.size = new_size;
		this.default_x_speed = new_base_speed;
	}

	this.reset = function(resize=false) {
		this.x_speed = this.default_x_speed * Math.sign(this.x_speed);
		if(!resize) {
			this.x_speed = -this.x_speed;
		}

		this.y_speed = getRandomArbitrary((-15 / 2) * (canvas.height / DEFAULT_HEIGHT), (15 / 2) * (canvas.height / DEFAULT_HEIGHT));
		this.x = canvas.width / 2;
		this.y = canvas.height / 2;
	}

	this.draw = function() {
		colorRect(this.x, this.y, this.size, this.size, 'white');
	}
}

function Paddle(x) {
	this.x = x;
	this.y = canvas.height / 2;
	this.height = 100;
	this.thickness = 10;

	this.resize = function(new_x, new_height, new_thickness) {
		this.x = new_x;
		this.height = new_height;
		this.thickness = new_thickness;

		CURRENT_PADDLE_HEIGHT = new_height;
	}

	this.reset = function(x) {
		this.x = x;
		this.y = canvas.height / 2;
	}

	this.draw = function(color='white') {
		colorRect(this.x, this.y, this.thickness, this.height, color);
	}
}


function Player(type) {
	this.type = type;
	this.mode = 'classic';
	this.score = 0;
	this.paddle = null;
	this.x = 0;
	this.paddle_thickness = 10;

	this.setup = function() {
		this.set_paddle_x_pos();

		this.paddle = new Paddle(this.x);
	};

	this.set_paddle_x_pos = function() {
		var wall_offset = DEFAULT_WALL_OFFSET * (canvas.width / DEFAULT_WIDTH);
		if(this.type === 'computer') {
			this.x = canvas.width - this.paddle_thickness - wall_offset;
		}
		else {
			this.x = wall_offset;
		}
	}

	this.reset = function() {
		this.paddle.reset(this.x);
		this.score = 0;
	}

	this.checkIfWon = function(game_settings) {
		if(this.score >= game_settings.winning_score && !game_settings.disable_endgame) {
			game_settings.showingWinScreen = true;
		}
	}

	this.resize = function() {
		this.paddle_thickness = canvas.width / 60;
		var paddle_height = canvas.height / 6;

		this.set_paddle_x_pos();

		this.paddle.resize(this.x, paddle_height, this.paddle_thickness);
	}

	this.draw = function() {
		this.paddle.draw();
	}

	this.manual_move = function(cursor) {
		if(cursor.y > this.paddle.height / 2 && cursor.y < canvas.height - this.paddle.height / 2) {
			this.paddle.y = cursor.y - (this.paddle.height / 2);
		}
	}

	this.auto_move = function(ball, game_settings) {
		var computerYCenter = this.paddle.y + (this.paddle.height / 2);

		if(computerYCenter < ball.y - ((this.paddle.height / 2)) * 0.35 && this.paddle.y + this.paddle.height < canvas.height) {
			this.paddle.y += game_settings.computer_speed() * this.paddle.height;
		}
		else if(computerYCenter > ball.y + ((this.paddle.height / 2)) * 0.35 && this.paddle.y > 0) {
			this.paddle.y -= game_settings.computer_speed() * this.paddle.height;
		}
	}

	// Execute on constructor instantiation;
	this.setup();
}

function GameSettings() {
	this.difficulty = 1;
	this.game_started = false;
	this.winning_score = 5;
	this.disable_endgame = false;
	this.showingWinScreen = false;

	this.set_difficulty = function(difficulty, computer) {
		if(difficulty === "easy") {
			this.difficulty = 1;
			computer.height = 0.9 * CURRENT_PADDLE_HEIGHT;
		}
		else if(difficulty === "medium") {
			this.difficulty = 2;
			computer.height = CURRENT_PADDLE_HEIGHT;
		}
		else {
			this.difficulty = 3;
			computer.height = 1.1 * CURRENT_PADDLE_HEIGHT;
		}
	}

	this.reset = function(ball, player1, computer) {
		ball.reset(true);
		player1.reset();
		computer.reset();

		this.showingWinScreen = false;
	}

	this.check_if_disable_endgame = function() {
		this.disable_endgame = this.winning_score === 0;  // if-else
	}

	this.ball_speed = function() {
		return 0.0075 * canvas.width;
	}

	this.computer_speed = function() {
		var speed;

		switch(this.difficulty) {
			case 1:
				speed = 0.04;
				break;

			case 2:
				speed = 0.06;
				break;

			case 3:
				speed = 0.08;
				break;

			default:
				speed = 0.06;
				break;
		}
		return speed;
	}
}

// ------------- /Construtores -------------


function moveEverything(ball, player1, computer, game_settings) {
	if(!game_settings.game_started || game_settings.showingWinScreen) {
		return;
	}

	computer.auto_move(ball, game_settings);

	ball.update();

	ball.handle_paddle_interaction(player1);
	ball.handle_paddle_interaction(computer);

	if(ball.scored()) {
		if(ball.x < canvas.width / 2) {
			computer.score++; // must be BEFORE ball.reset()
			computer.checkIfWon(game_settings);
		}
		else {
			player1.score++; // must be BEFORE ball.reset()
			player1.checkIfWon(game_settings);
		}
		ball.reset();
	}
}

function drawEverything(ball, player1, computer, game_settings) {
	// next line blanks out the screen with black
	colorRect(0, 0, canvas.width, canvas.height, 'black');

	canvasContext.font = baseTextSize + " Bit5x3";
	canvasContext.textAlign = "center";

	if(isTouchScreen()) {
		var interaction = "toque";
	} else {
		var interaction = "clique";
	}

	if(!game_settings.game_started) {
		canvasContext.fillStyle = 'white';
		canvasContext.font = "64px Bit5x3";
		canvasContext.fillText("Pong", (canvas.width) / 2, canvas.height / 3);

		canvasContext.font = "20px Bit5x3";
		canvasContext.fillText(interaction + " para comecar", (canvas.width / 2), 5 * canvas.height / 6);

		return;
	}

	if(game_settings.showingWinScreen) {
		win_text = "Voce ganhou!!";
		lose_text = "Voce perdeu =(";

		canvasContext.fillStyle = 'white';

		if(player1.score > computer.score) {
			canvasContext.fillText(win_text, (canvas.width) / 2, canvas.height / 3);
		}
		else {
			canvasContext.fillText(lose_text, (canvas.width) / 2, canvas.height / 3);
		}

		canvasContext.fillText(interaction + " para reiniciar", (canvas.width) / 2, 5 * canvas.height / 6);
		return;
	}

	drawNet();

	// this is left player paddle
	player1.draw();

	// this is left computer paddle
	computer.draw();

	// next line draws the ball
	ball.draw();

	// player and computer scores
	canvasContext.fillText(player1.score, 100 * (canvas.width / DEFAULT_WIDTH), canvas.height / 6);
	canvasContext.fillText(computer.score, (DEFAULT_WIDTH - 100) * (canvas.width / DEFAULT_WIDTH), canvas.height / 6);
}


// ---------- Auxiliary Functions ----------

function getRandomArbitrary(min, max) {
	// https://developer.mozilla.org/pt-BR/docs/Web/JavaScript/Reference/Global_Objects/Math/random
	return Math.random() * (max - min) + min;
}

function drawNet() {
	for(var i = 0; i < canvas.height; i += 40) {
		colorRect((canvas.width / 2) -1, i, 2, 20, 'white');
	}
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

function colorCircle(centerX, centerY, radius, drawColor) {
	// (http://www.w3schools.com/tags/canvas_arc.asp)
	// Método .arc(a, b, c, d, e, f):
	//		a. [posição x do centro da circunferência],
	// 		b. [posição y do centro da circunferência],
	//		c. [raio da circunferência],
	//		d. [ângulo de início do desenho],
	//		e. [ângulo final do desenho],
	//		f. [Default: false; Indica se o desenho deve ser feito no sentido horário ou anti-horário. Não faz diferença se é uma circunferência completa]

	canvasContext.fillStyle = drawColor;
	canvasContext.beginPath(); // requisito para definir uma forma não retangular
	canvasContext.arc(centerX, centerY, radius, 0, Math.PI*2, true);
	canvasContext.fill();
}

function isTouchScreen() {
	return window.matchMedia('(hover: none)').matches;
}
