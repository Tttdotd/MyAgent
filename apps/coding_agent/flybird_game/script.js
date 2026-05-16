// Get DOM elements
const canvas = document.getElementById('game-canvas');
const ctx = canvas.getContext('2d');
const startBtn = document.getElementById('start-btn');
const pauseBtn = document.getElementById('pause-btn');
const scoreEl = document.getElementById('score');
const historyEl = document.getElementById('history');
const welcomeScreen = document.getElementById('welcome-screen');
const startBtnWelcome = document.getElementById('start-btn-welcome');

// Game variables
let gameRunning = false;
let gamePaused = false;
let score = 0;
let history = [];
let lastTime = 0;
let deltaTime = 0;

// Bird properties
const bird = {
    x: 50,
    y: 300,
    width: 34,
    height: 24,
    velocity: 0,
    gravity: 0.5,
    jumpStrength: -8
};

// Pipes properties
let pipes = [];
const pipeGap = 150;
const pipeDistance = 200; // Now interpreted as pixel distance between pipes
const pipeWidth = 60;
let pipeDistanceCounter = 0; // New counter for horizontal movement

// Background color
const skyColor = '#7fb3d5';

// Sound effect simulation (optional)
function playSound(type) {
    const audio = new Audio();
    switch(type) {
        case 'jump':
            audio.src = 'data:audio/wav;base64,UklGRigAAABXRUJQVlA4TBEAAAAvAAAAAAfQ//7/AxoAVwB9AA==';
            break;
        case 'score':
            audio.src = 'data:audio/wav;base64,UklGRigAAABXRUJQVlA4TBEAAAAvAAAAAAfQ//7/AxoAVwB9AA==';
            break;
        default:
            return;
    }
    audio.volume = 0.2;
    audio.play().catch(e => console.log('Audio playback blocked'));
}

// Draw bird
function drawBird() {
    ctx.fillStyle = 'yellow';
    ctx.fillRect(bird.x, bird.y, bird.width, bird.height);
    
    // Draw eye
    ctx.fillStyle = 'black';
    ctx.beginPath();
    ctx.arc(bird.x + 28, bird.y + 12, 4, 0, Math.PI * 2);
    ctx.fill();
}

// Draw pipes
function drawPipes() {
    ctx.fillStyle = 'green';
    pipes.forEach(pipe => {
        // Top pipe: from top (0) to pipe.height
        ctx.fillRect(pipe.x, 0, pipeWidth, pipe.height);
        
        // Bottom pipe: from pipe.height + pipeGap to bottom
        ctx.fillRect(pipe.x, pipe.height + pipeGap, pipeWidth, canvas.height - (pipe.height + pipeGap));
    });
}

// Update bird position
function updateBird() {
    if (!gameRunning || gamePaused) return;
    
    bird.velocity += bird.gravity;
    bird.y += bird.velocity;
    
    // Ground collision
    if (bird.y + bird.height > canvas.height) {
        gameOver();
    }
    
    // Ceiling collision
    if (bird.y < 0) {
        gameOver();
    }
}

// Create new pipe
function createPipe() {
    const minHeight = 50;
    const maxHeight = canvas.height - pipeGap - minHeight;
    const height = Math.floor(Math.random() * (maxHeight - minHeight + 1)) + minHeight;
    
    pipes.push({
        x: canvas.width,
        y: 0,
        height: height,
        passed: false
    });
}

// Update pipes
function updatePipes() {
    if (!gameRunning || gamePaused) return;
    
    // Move pipes and check for new pipe generation
    pipes.forEach(pipe => {
        pipe.x -= 2; // Move left by 2 pixels per frame
        
        // Check if bird passed the pipe
        if (!pipe.passed && pipe.x + pipeWidth < bird.x) {
            pipe.passed = true;
            score += 1;
            scoreEl.textContent = `得分: ${score}`;
            scoreEl.classList.add('shake');
            setTimeout(() => scoreEl.classList.remove('shake'), 500);
            playSound('score');
        }
        
        // Collision detection
        if (
            bird.x + bird.width > pipe.x &&
            bird.x < pipe.x + pipeWidth &&
            (bird.y < pipe.height || bird.y + bird.height > pipe.height + pipeGap)
        ) {
            gameOver();
        }
    });
    
    // Add to distance counter
    pipeDistanceCounter += 2; // Accumulate movement in pixels
    
    // Create new pipe when distance threshold reached
    if (pipeDistanceCounter >= pipeDistance) {
        createPipe();
        pipeDistanceCounter = 0; // Reset counter
    }
    
    // Remove pipes that are off-screen
    pipes = pipes.filter(pipe => pipe.x + pipeWidth > 0);
}

// Game over function
function gameOver() {
    gameRunning = false;
    history.push(score);
    historyEl.innerHTML = `历史记录: ${history.join(', ')}`;
    alert(`游戏结束！得分: ${score}`);
}

// Start game
function startGame() {
    if (gameRunning) return;
    
    gameRunning = true;
    gamePaused = false;
    score = 0;
    scoreEl.textContent = `得分: ${score}`;
    pipes = [];
    bird.y = 300;
    bird.velocity = 0;
    
    // Reset history display
    historyEl.innerHTML = `历史记录: ${history.join(', ')}`;
    
    // Initialize pipe distance counter and create first pipe
    pipeDistanceCounter = 0; // Reset counter
    createPipe();   // Create first pipe immediately
    
    // Hide welcome screen
    welcomeScreen.style.display = 'none';
    
    // Start animation loop
    lastTime = performance.now();
    animate();
    playSound('jump');
}

// Pause game
function pauseGame() {
    if (!gameRunning) return;
    
    gamePaused = !gamePaused;
    pauseBtn.textContent = gamePaused ? '继续游戏' : '暂停游戏';
    
    // If resuming, restart animation loop
    if (!gamePaused && gameRunning) {
        requestAnimationFrame(animate);
    }
}

// Animation loop
function animate(time) {
    deltaTime = (time - lastTime) / 1000;
    lastTime = time;
    
    // Clear canvas
    ctx.fillStyle = skyColor;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Update and draw
    updateBird();
    updatePipes();
    drawBird();
    drawPipes();
    
    // Continue animation if running and not paused
    if (gameRunning && !gamePaused) {
        requestAnimationFrame(animate);
    }
}

// Event listeners
startBtn.addEventListener('click', startGame);
pauseBtn.addEventListener('click', pauseGame);
startBtnWelcome.addEventListener('click', startGame); // Add listener for welcome button

// Keyboard controls
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space') {
        e.preventDefault();
        if (gameRunning) {
            if (gamePaused) {
                pauseGame();
            } else {
                bird.velocity = bird.jumpStrength;
                playSound('jump');
            }
        } else {
            startGame();
        }
    }
});

// Touch controls for mobile
canvas.addEventListener('touchstart', () => {
    if (gameRunning) {
        if (gamePaused) {
            pauseGame();
        } else {
            bird.velocity = bird.jumpStrength;
            playSound('jump');
        }
    } else {
        startGame();
    }
});