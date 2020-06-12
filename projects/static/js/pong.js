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

function handleMouseClick(evt, ball, player1, computer, game) {
	if(!game.started) {
		game.started = true;
		game.reset(ball, player1, computer);
	}

	if(game.showingWinScreen) {
		player1.score = 0;
		computer.score = 0;
		game.showingWinScreen = false;
	}
}

// ------------- /Cursor Handling Functions -------------

// -------------- Global functions --------------

function displaySettings(reload, reset, game, ball=null, player1=null, computer=null) {
	var deviceHeight = document.documentElement.clientHeight;
	var deviceWidth = document.documentElement.clientWidth;
	try {
		var ratio = game.mode_info[game.mode]["canvas_ratio"];  // screen aspect ratio;
	}
	catch (e) {
		var ratio = 0.75;  // default aspect ratio: 3 by 4
	}

	var available_height = deviceHeight - SETTINGS_HEIGHT - CANVAS_HEIGHT_PADDING;

	if(deviceWidth < 350) {
		if(available_height < deviceWidth - 50 && available_height / ratio < deviceWidth - 50) {
			canvas.height = available_height;
			canvas.width = canvas.height / ratio;
		}
		else {
			canvas.width = deviceWidth - 50;
			canvas.height = ratio * canvas.width;
		}

		controls.style.width = (canvas.width).toString() + "px";
		baseTextSize = "20px";
	}
	else if(deviceWidth < 576) {
		if(available_height < deviceWidth - 50 && available_height / ratio < deviceWidth - 50) {
			canvas.height = available_height;
			canvas.width = canvas.height / ratio;
		}
		else {
			canvas.width = deviceWidth - 50;
			canvas.height = ratio * canvas.width;
		}

		controls.style.width = (canvas.width).toString() + "px";
		baseTextSize = "24px";
	}
	else if(719 < deviceWidth && deviceWidth < 768) {
		if(available_height < 0.6 * deviceWidth && available_height / ratio < 0.6 * deviceWidth) {
			canvas.height = available_height;
			canvas.width = canvas.height / ratio;
		}
		else {
			canvas.width = 0.6 * deviceWidth;
			canvas.height = ratio * canvas.width;
		}

		controls.style.width = (canvas.width).toString() + "px";
		baseTextSize = "32px";
	}
	else if(deviceWidth < 992) {
		if(available_height < 0.7 * deviceWidth && available_height / ratio < 0.7 * deviceWidth) {
			canvas.height = available_height;
			canvas.width = canvas.height / ratio;
		}
		else {
			canvas.width = 0.7 * deviceWidth;
			canvas.height = ratio * canvas.width;
		}
		canvas.width = 0.7 * deviceWidth;
		canvas.height = ratio * canvas.width;

		controls.style.width = (canvas.width).toString() + "px";
		baseTextSize = "32px";
	}
	else if(deviceWidth < 1200) {
		if(available_height < 0.6 * deviceWidth && available_height / ratio < 0.6 * deviceWidth) {
			canvas.height = available_height;
			canvas.width = canvas.height / ratio;
		}
		else {
			canvas.width = 0.6 * deviceWidth;
			canvas.height = ratio * canvas.width;
		}

		controls.style.width = (canvas.width).toString() + "px";
		baseTextSize = "32px";
	}
	else {
		if(available_height < DEFAULT_HEIGHT) {
			canvas.height = available_height;
			canvas.width = canvas.height / ratio;
		}
		else {
			canvas.width = DEFAULT_WIDTH;
			canvas.height = ratio * canvas.width;
		}

		controls.style.width = (canvas.width).toString() + "px";
		baseTextSize = "32px";
	}

	if(reload) {
		player1.resize();
		computer.resize();
		ball.resize(canvas.width / 60, game.ball_speed());

		game.started = false;

		if(reset) {
			game.reset(ball, player1, computer);
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
	var game = new Game();
	var ball = new Ball(game.ball_speed());
	var player1 = new Player('person');
	var computer = new Player('computer');

	displaySettings(true, false, game, ball, player1, computer);

	// Difficulty selection
	var difficulty_selector = document.getElementById('difficulty');
	game.set_difficulty(difficulty_selector[difficulty_selector.selectedIndex].value, computer);

	// Score selection
	var score_selector = document.getElementById('max-score');
	game.winning_score = Number(score_selector[score_selector.selectedIndex].value);
	game.check_if_disable_endgame();

	setInterval(function() {
		game.moveEverything(ball, player1, computer);
		game.drawEverything(ball, player1, computer);
	}, 1000/framesPerSecond);

	// Método .addEventListener (http://www.w3schools.com/jsref/met_element_addeventlistener.asp)
	canvas.addEventListener('mousemove', // http://www.w3schools.com/jsref/dom_obj_event.asp
		function(evt) {
			var mousePos = calculateMousePos(evt);
			if(game.started) {
				player1.manual_move(mousePos);
			}
		});

	canvas.addEventListener('touchmove', // http://www.w3schools.com/jsref/dom_obj_event.asp
		function(evt) {
			var touchPos = calculateTouchPos(evt);
			if(game.started) {
				player1.manual_move(touchPos);
			}
		});

	canvas.addEventListener('mousedown', function(evt) {
		handleMouseClick(evt, ball, player1, computer, game);
	});

	window.addEventListener("resize", function(event) {
		displaySettings(true, true, game, ball, player1, computer);

		// Makes sure the correct computer paddle height is enabled
		game.set_difficulty(difficulty_selector[difficulty_selector.selectedIndex].value, computer);
	});

	$('a[data-toggle="tab"]').on('shown.bs.tab', function(e) {
		var target = $(e.target).attr("href"); // activated tab

		game.set_mode(target.substring(1), player1, computer);
		displaySettings(true, true, game, ball, player1, computer);
	});

	difficulty_selector.addEventListener('change', function(event) {
		game.set_difficulty(difficulty_selector[difficulty_selector.selectedIndex].value, computer);

		// When difficulty level is changed, game is reseted
		game.reset(ball, player1, computer);
	});

	score_selector.addEventListener('change', function(event) {
		game.winning_score = Number(score_selector[score_selector.selectedIndex].value);
		game.check_if_disable_endgame();
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
		for(i = 0; i < player.num_paddles; i++) {
			if(this.check_if_hit_paddle(player.paddles[i])) {
				if(player.mode !== 'tennis' || ((player.type === 'person' && this.x_speed < 0) || (player.type === 'computer' && this.x_speed > 0))) {
					this.x_speed = -this.x_speed;
				}

				var deltaY = this.y - (player.paddles[i].y + (player.paddles[i].height / 2));
				this.y_speed = deltaY * 0.2;
			}
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
	this.num_paddles = 1;
	this.score = 0;
	this.paddles = null;
	this.x = [0, 0];
	this.paddle_thickness = 10;

	this.setup = function() {
		this.set_paddle_x_pos();

		this.paddles = [new Paddle(this.x[0]), new Paddle(this.x[1])];
	};

	this.set_mode = function(mode) {
		if(mode === 'classic') {
			this.mode = mode;
			this.num_paddles = 1;
		}
		else if(mode === 'tennis') {
			this.mode = mode;
			this.num_paddles = 2;
		}
	}

	this.set_paddle_x_pos = function() {
		var wall_offset = DEFAULT_WALL_OFFSET * (canvas.width / DEFAULT_WIDTH);
		if(this.type === 'computer') {
			this.x[0] = canvas.width - this.paddle_thickness - wall_offset;
			this.x[1] = 0.625 * canvas.width;
		}
		else {
			this.x[0] = wall_offset;
			this.x[1] = 0.375 * canvas.width;
		}
	}

	this.reset = function() {
		for(i = 0; i < this.paddles.length; i++) {
			this.paddles[i].reset(this.x[i]);
		}
		this.score = 0;
	}

	this.checkIfWon = function(game) {
		if(this.score >= game.winning_score && !game.disable_endgame) {
			game.showingWinScreen = true;
		}
	}

	this.resize = function() {
		this.paddle_thickness = canvas.width / 60;
		var paddle_height = canvas.height / 6;

		this.set_paddle_x_pos();

		for(i = 0; i < this.paddles.length; i++) {
			this.paddles[i].resize(this.x[i], paddle_height, this.paddle_thickness);
		}
	}

	this.draw = function() {
		for(i = 0; i < this.num_paddles; i++) {
			this.paddles[i].draw();
		}
	}

	this.manual_move = function(cursor) {
		if(cursor.y > this.paddles[0].height / 2 && cursor.y < canvas.height - this.paddles[0].height / 2) {
			this.paddles[0].y = cursor.y - (this.paddles[0].height / 2);
		}

		if(this.mode === 'tennis') {
			this.paddles[1].y = canvas.height - (this.paddles[0].height + this.paddles[0].y); 
		}
	}

	this.auto_move = function(ball, game) {
		var variability = (this.type === 'person') ? 1.05 : 1;
		var computerYCenter = this.paddles[0].y + (this.paddles[0].height / 2);

		if(computerYCenter < ball.y - ((this.paddles[0].height / 2)) * 0.35 && this.paddles[0].y + this.paddles[0].height < canvas.height) {
			this.paddles[0].y += variability * game.computer_speed() * this.paddles[0].height;
		}
		else if(computerYCenter > ball.y + ((this.paddles[0].height / 2)) * 0.35 && this.paddles[0].y > 0) {
			this.paddles[0].y -= variability * game.computer_speed() * this.paddles[0].height;
		}

		if(this.mode === 'tennis') {
			this.paddles[1].y = canvas.height - (this.paddles[0].height + this.paddles[0].y); 
		}
	}

	// Execute on constructor instantiation;
	this.setup();
}

function Game() {
	this.difficulty = 1;
	this.mode = 'classic';
	this.mode_info = {
		"classic": {
			"game_name": "Pong",
			"background_color": "black",
			"canvas_ratio": 0.75  // 3 by 4 aspect ratio
		},
		"tennis": {
			"game_name": "Pong Tennis",
			"background_color": "#A73202",
			"canvas_ratio": 0.625  // 1 by 2 aspect ratio
		},
		"football": {
			"game_name": "Pong Soccer",
			"background_color": "#28A745",
			"canvas_ratio": 0.64  // 16 by 25 aspect ratio
		},
	}
	this.started = false;
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

	this.set_mode = function(mode, player1, computer) {
		player1.set_mode(mode);
		computer.set_mode(mode);

		this.mode = mode;
		this.started = false;
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

	this.drawFieldLines = function() {
		if(this.mode === 'classic') {
			for(var i = 0; i < canvas.height; i += 40) {
				colorRect((canvas.width / 2) - 1, i, 2, 20, 'white');
			}
		}

		if(this.mode === 'tennis') {
			for(var i = 0; i < canvas.height; i += 30) {
				colorRect((canvas.width / 2) - 1, i, 2, 15, 'white');
			}
			colorRect(0, (0.125 * canvas.height) - 1, canvas.width, 2, 'white');
			colorRect(0.25 * canvas.width, 0.125 * canvas.height, 2, 0.75 * canvas.height, 'white');
			colorRect(0.25 * canvas.width, (canvas.height / 2) - 1, 0.5 * canvas.width, 2, 'white');
			colorRect(0.75 * canvas.width, 0.125 * canvas.height, 2, 0.75 * canvas.height, 'white');
			colorRect(0, (0.875 * canvas.height) - 1, canvas.width, 2, 'white');
		}
	}

	this.moveEverything = function(ball, player1, computer) {
		if(this.showingWinScreen) {
			return;
		}

		if(!this.started) {
			player1.auto_move(ball, this);
		}

		computer.auto_move(ball, this);

		ball.update();

		ball.handle_paddle_interaction(player1);
		ball.handle_paddle_interaction(computer);

		if(ball.scored()) {
			if(ball.x < canvas.width / 2) {
				computer.score++; // must be BEFORE ball.reset()
				if(this.started) { computer.checkIfWon(this); }
			}
			else {
				player1.score++; // must be BEFORE ball.reset()
				if(this.started) { player1.checkIfWon(this); }
			}
			ball.reset();
		}
	}

	this.drawEverything = function(ball, player1, computer) {
		// next line blanks out the screen with black
		colorRect(0, 0, canvas.width, canvas.height, this.mode_info[this.mode]["background_color"]);

		canvasContext.font = baseTextSize + " Bit5x3";
		canvasContext.textAlign = "center";

		if(isTouchScreen()) {
			var interaction = "toque";
		} else {
			var interaction = "clique";
		}

		if(!this.started) {
			canvasContext.fillStyle = 'white';
			var title = this.mode_info[this.mode]["game_name"];
			var deviceWidth = document.documentElement.clientWidth;

			if(title.split(" ").length > 1 && deviceWidth < 450) {
				canvasContext.font = "48px Bit5x3";
				canvasContext.fillText(title.split(" ")[0], (canvas.width) / 2, (canvas.height / 6) + 10);
				canvasContext.fillText(title.split(" ")[1], (canvas.width) / 2, (canvas.height / 3) + 20);
			}
			else {
				canvasContext.font = "64px Bit5x3";
				canvasContext.fillText(title, (canvas.width) / 2, canvas.height / 3);
			}

			canvasContext.font = "20px Bit5x3";
			canvasContext.fillText(interaction + " para comecar", (canvas.width / 2), 5 * canvas.height / 6);

			// return;
		}

		if(this.showingWinScreen) {
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

		this.drawFieldLines();

		// this is left player paddle
		player1.draw();

		// this is left computer paddle
		computer.draw();

		// next line draws the ball
		ball.draw();

		var score_height = (this.mode === 'tennis') ? canvas.height / 10 : canvas.height / 6;

		// player and computer scores
		canvasContext.fillText(player1.score, 100 * (canvas.width / DEFAULT_WIDTH), score_height);
		canvasContext.fillText(computer.score, (DEFAULT_WIDTH - 100) * (canvas.width / DEFAULT_WIDTH), score_height);
	}
}

// ------------- /Construtores -------------

// ---------- Auxiliary Functions ----------

function getRandomArbitrary(min, max) {
	// https://developer.mozilla.org/pt-BR/docs/Web/JavaScript/Reference/Global_Objects/Math/random
	return Math.random() * (max - min) + min;
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
