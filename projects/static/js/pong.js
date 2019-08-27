var canvas;
var canvasContext;
var controls;
var showingWinScreen = false;
var gameStarted = false;

var WINNING_SCORE = 5;
var disable_endgame = false;

var DEFAULT_WIDTH;
var DEFAULT_HEIGHT;
var PADDLE_HEIGHT = 100;
var PADDLE_THICKNESS = 10;
var BALL_SIZE = 10;

// ------------- Cálculo do Mouse -------------

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

function handleMouseClick(evt, player1, computer) {
	if(!gameStarted) {
		gameStarted = true;
	}

	if(showingWinScreen) {
		player1.score = 0;
		computer.score = 0;
		showingWinScreen = false;
	}
}

// ------------- /Cálculo do Mouse -------------

// -------------- Global functions --------------

function reset_game(ball, player1, computer) {
	ball.reset();
	player1.reset(0);
	computer.reset(canvas.width - PADDLE_THICKNESS);

	showingWinScreen = false;
	game_ended = false;
}

function displaySettings(reload, reset, ball=null, player1=null, computer=null) {
	if(window.innerWidth < 575) {
		canvas.width = window.innerWidth - 50;
		canvas.height = 0.75 * canvas.width;
		controls.style.width = (canvas.width).toString() + "px";
	}
	else if(window.innerWidth < 650) {
		canvas.width = 0.8 * window.innerWidth;
		canvas.height = 0.75 * canvas.width;
		controls.style.width = (canvas.width).toString() + "px";
	}
	else if(window.innerWidth < 767) {
		canvas.width = 0.7 * window.innerWidth;
		canvas.height = 0.75 * canvas.width;
		controls.style.width = (canvas.width).toString() + "px";
	}
	else if(window.innerWidth < 990) {
		canvas.width = 0.6 * window.innerWidth;
		canvas.height = 0.75 * canvas.width;
		controls.style.width = (canvas.width).toString() + "px";
	}
	else {
		canvas.width = DEFAULT_WIDTH;
		canvas.height = DEFAULT_HEIGHT;
		controls.style.width = (canvas.width).toString() + "px";
	}

	if(reload) {
		PADDLE_HEIGHT = canvas.height / 6;
		PADDLE_THICKNESS = canvas.width / 60;
		BALL_SIZE = canvas.width / 60;

		gameStarted = false;

		if(reset) {
			reset_game(ball, player1, computer);
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

	DEFAULT_WIDTH = canvas.width;
	DEFAULT_HEIGHT = canvas.height;

	displaySettings(true, false);

	var score_selector = document.getElementById('max-score');

	WINNING_SCORE = Number(score_selector[score_selector.selectedIndex].value);
	disable_endgame = WINNING_SCORE === 0;  // if-else

	var framesPerSecond = 30;
	var ball = new Ball();
	var player1 = new Paddle(0);
	var computer = new Paddle(canvas.width - PADDLE_THICKNESS);

	setInterval(function() {
		moveEverything(ball, player1, computer);
		drawEverything(ball, player1, computer);
	}, 1000/framesPerSecond);

	// Método .addEventListener (http://www.w3schools.com/jsref/met_element_addeventlistener.asp)
	canvas.addEventListener('mousemove', // http://www.w3schools.com/jsref/dom_obj_event.asp
		function(evt) {
			var mousePos = calculateMousePos(evt);
			if(mousePos.y > player1.height / 2 && mousePos.y < canvas.height - player1.height / 2) {
				player1.y = mousePos.y - (player1.height / 2);
			}
		});

	canvas.addEventListener('mousedown', function(evt) {
		handleMouseClick(evt, player1, computer);
	});

	window.addEventListener("resize", function(event) {
		displaySettings(true, true, ball, player1, computer);
	});

	score_selector.addEventListener('change', function(event) {
		WINNING_SCORE = Number(score_selector[score_selector.selectedIndex].value);

		disable_endgame = WINNING_SCORE === 0;  // if-else
	});
}

// ------------------- /Main -------------------

// ---------------- Construtores ----------------

function Ball() {
	this.x = 110;
	this.y = 50;
	this.x_speed = 10;
	this.y_speed = 4;
	this.size = BALL_SIZE;

	this.update = function() {
		this.x += this.x_speed;
		this.y += this.y_speed;

		if(this.y > canvas.height || this.y < 0) {
			this.y_speed = -this.y_speed;
		}

		// if(this.x > canvas.width || this.x < 0) {
		// 	this.x_speed = -this.x_speed;
		// }
	}

	this.reset = function() {
		this.x_speed = -this.x_speed;
		this.y_speed = getRandomArbitrary(-15 * (canvas.height / DEFAULT_HEIGHT), 15 * (canvas.height / DEFAULT_HEIGHT));
		this.x = canvas.width / 2;
		this.y = canvas.height / 2;
		this.size = BALL_SIZE;
	}

	this.draw = function() {
		colorRect(this.x - (this.size / 2), this.y - (this.size / 2), this.size, this.size, 'white');
	}
}

function Paddle(x) {
	this.x = x;
	this.y = canvas.height / 2;
	this.height = PADDLE_HEIGHT;
	this.thickness = PADDLE_THICKNESS;
	this.score = 0;

	this.reset = function(x) {
		this.x = x;
		this.y = canvas.height / 2;
		this.height = PADDLE_HEIGHT;
		this.thickness = PADDLE_THICKNESS;
		this.score = 0;
	}

	this.checkIfWon = function() {
		if(this.score >= WINNING_SCORE && !disable_endgame) {
			showingWinScreen = true;
		}
	}

	this.draw = function(color = 'white') {
		colorRect(this.x, this.y, this.thickness, this.height, color);
	}
}

// ------------- /Construtores -------------


function computerMovement(ball, computer) {
	var computerYCenter = computer.y + (computer.height / 2);

	if(computerYCenter < ball.y - ((computer.height / 2)) * 0.35 && computer.y + computer.height < canvas.height) {
		computer.y += 6;
	} else if(computerYCenter > ball.y + ((computer.height / 2)) * 0.35 && computer.y > 0) {
		computer.y -= 6;
	}
}

function moveEverything(ball, player1, computer) {
	if(!gameStarted || showingWinScreen) {
		return;
	}

	computerMovement(ball, computer);

	ball.update();

	if(ball.x < PADDLE_THICKNESS) {
		if(ball.y > player1.y && ball.y < (player1.y + player1.height)) {
			ball.x_speed = -ball.x_speed;

			var deltaY = ball.y - (player1.y + (player1.height / 2));
			ball.y_speed = deltaY * 0.35;

		} else {

			computer.score++; // must be BEFORE ball.reset()
			computer.checkIfWon();

			ball.reset();
		}
	}

	if(ball.x > canvas.width - PADDLE_THICKNESS) {
		if(ball.y > computer.y && ball.y < (computer.y + computer.height)) {
			ball.x_speed = -ball.x_speed;

			var deltaY = ball.y - (computer.y + (computer.height / 2));
			ball.y_speed = deltaY * 0.35;

		} else {

			player1.score++; // must be BEFORE ball.reset()
			player1.checkIfWon();

			ball.reset();
		}
	}

	//console.log(ballX);
}

function drawEverything(ball, player1, computer) {
	// next line blanks out the screen with black
	colorRect(0, 0, canvas.width, canvas.height, 'black');

	canvasContext.font = "2rem Bit5x3";

	if(!gameStarted) {
		canvasContext.fillStyle = 'white';
		canvasContext.font = "4rem Bit5x3";
		canvasContext.fillText("Pong", (canvas.width - 125) / 2, canvas.height / 3);

		canvasContext.font = "1.25rem Bit5x3";
		canvasContext.fillText("clique para comecar", (canvas.width / 2) - 100, 5 * canvas.height / 6);

		return;
	}

	if(showingWinScreen) {
		win_text = "Voce ganhou!!";
		lose_text = "Voce perdeu =(";

		canvasContext.fillStyle = 'white';

		if(player1.score > computer.score) {
			canvasContext.fillText(win_text, (canvas.width - 16 * win_text.length) / 2, canvas.height / 3);
		}
		else {
			canvasContext.fillText(lose_text, (canvas.width - 16 * lose_text.length) / 2, canvas.height / 3);
		}

		canvasContext.fillText("clique para reiniciar", (canvas.width - 350) / 2, 5 * canvas.height / 6);
		return;
	}

	drawNet();

	// this is left player paddle
	player1.draw();

	// this is left computer paddle
	computer.draw();

	// next line draws the ball
	ball.draw();

	// 2 digits offset
	var player_score_draw_offset = 0;
	if(player1.score < 10) {
		player_score_draw_offset = 30;
	}
	var computer_score_draw_offset = 0;
	if(computer.score >= 10) {
		computer_score_draw_offset = 30;
	}

	// player and computer scores
	canvasContext.fillText(player1.score, (70 + player_score_draw_offset) * (canvas.width / DEFAULT_WIDTH), canvas.height / 6);
	canvasContext.fillText(computer.score, (DEFAULT_WIDTH - (100 + computer_score_draw_offset)) * (canvas.width / DEFAULT_WIDTH), canvas.height / 6);

}


// ---------- Funções auxiliares ----------

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