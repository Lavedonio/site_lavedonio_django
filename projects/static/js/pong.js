var canvas;
var canvasContext;
var showingWinScreen = false;
var gameStarted = false;

const WINNING_SCORE = 5;
const PADDLE_HEIGHT = 100;
const PADDLE_THICKNESS = 10;

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

// -------------------- Main --------------------

window.onload = function() {
	// window.onload associado a função: carrega o que tiver dentro apenas depois que a página terminar de carregar
	canvas = document.getElementById('gameCanvas'); //associa a variável canvas ao elemento no HTML
	canvasContext = canvas.getContext('2d');

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
}

// ------------------- /Main -------------------

// ---------------- Construtores ----------------

function Ball() {
	this.x = 110;
	this.y = 50;
	this.x_speed = 10;
	this.y_speed = 4;
	this.size = 10;

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
		this.y_speed = getRandomArbitrary(-15, 15);
		this.x = canvas.width / 2;
		this.y = canvas.height / 2;
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

	this.checkIfWon = function() {
		if(this.score >= WINNING_SCORE) {
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

	canvasContext.font = "20px Helvetica";

	if(!gameStarted) {
		canvasContext.fillStyle = 'white';
		canvasContext.font = "40px Helvetica";
		canvasContext.fillText("Pong", (canvas.width - 100) / 2, canvas.height / 3);

		canvasContext.font = "20px Helvetica";
		canvasContext.fillText("clique para começar", (canvas.width / 2) - 90, 5 * canvas.height / 6);

		return;
	}

	if(showingWinScreen) {
		win_text = "Você ganhou!!";
		lose_text = "Você perdeu =(";

		canvasContext.fillStyle = 'white';

		if(player1.score >= WINNING_SCORE) {
			canvasContext.fillText(win_text, (canvas.width - 10 * win_text.length) / 2, canvas.height / 3);
		} else if(computer.score >= WINNING_SCORE) {
			canvasContext.fillText(lose_text, (canvas.width - 10 * lose_text.length) / 2, canvas.height / 3);
		}

		canvasContext.fillText("clique para reiniciar", (canvas.width / 2) - 90, 5 * canvas.height / 6);
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
	canvasContext.fillText(player1.score, 100, 100);
	canvasContext.fillText(computer.score, canvas.width - 100, 100);

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