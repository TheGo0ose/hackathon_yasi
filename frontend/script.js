// ── VIEW ROUTING ──
function showView(viewId) {
    const views = ['view-landing', 'view-form', 'view-result', 'view-chat', 'view-calc', 'view-import'];
    views.forEach(id => {
        const el = document.getElementById(id);
        if (id === viewId) {
            el.classList.remove('view-hidden');
            el.style.display = 'flex';
            // Trigger animation trick
            el.style.opacity = '0';
            setTimeout(() => { el.style.opacity = '1'; }, 50);
        } else {
            el.classList.add('view-hidden');
            el.style.display = 'none';
        }
    });
}

// ── SMOKE CANVAS EFFECT ──
const canvas = document.getElementById('smoke-canvas');
const ctx = canvas.getContext('2d');
let reqAnimFrame;

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

const particles = [];
for (let i = 0; i < 60; i++) {
    particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 1.5,
        vy: (Math.random() - 0.5) * 1.5,
        radius: 60 + Math.random() * 80,
        alpha: 0.05 + Math.random() * 0.1
    });
}

let pointer = { x: canvas.width / 2, y: canvas.height / 2 };
let lastPointer = { x: canvas.width / 2, y: canvas.height / 2 };
let cursorSpeed = 0;

window.addEventListener('mousemove', (e) => {
    lastPointer.x = pointer.x;
    lastPointer.y = pointer.y;
    pointer.x = e.clientX;
    pointer.y = e.clientY;
    
    let dx = pointer.x - lastPointer.x;
    let dy = pointer.y - lastPointer.y;
    cursorSpeed = Math.min(Math.sqrt(dx * dx + dy * dy), 100); // cap speed metric
});

function renderCanvas() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Set global mixture mode similar to screen
    ctx.globalCompositeOperation = 'screen';
    
    // Decay cursor speed naturally if mouse stops
    cursorSpeed *= 0.92;

    for (let p of particles) {
        // dynamic opacity and size based on cursor movement intensity
        let dynamicAlpha = p.alpha + (cursorSpeed * 0.003);
        let dynamicRadius = p.radius + (cursorSpeed * 0.5);

        p.x += p.vx;
        p.y += p.vy;
        
        let dx = pointer.x - p.x;
        let dy = pointer.y - p.y;
        let dist = Math.sqrt(dx * dx + dy * dy);
        
        if (dist < 400 + (cursorSpeed * 2)) {
            // Intensity scaling
            let strength = 0.5 + (cursorSpeed * 0.05);
            p.vx += (dx / dist) * strength;
            p.vy += (dy / dist) * strength;
        } else {
            // Drift away logic (slowly expand towards edges if not near cursor)
            p.vx += (p.x > canvas.width / 2 ? 0.05 : -0.05);
            p.vy += (p.y > canvas.height / 2 ? 0.05 : -0.05);
        }
        
        const speed = Math.sqrt(p.vx * p.vx + p.vy * p.vy);
        const maxSpeed = 12 + (cursorSpeed * 0.3);
        if (speed > maxSpeed) {
            p.vx = (p.vx / speed) * maxSpeed;
            p.vy = (p.vy / speed) * maxSpeed;
        }
        
        p.vx *= 0.95;
        p.vy *= 0.95;
        
        // Ambient flow
        p.vx += (Math.random() - 0.5) * 0.1;
        p.vy += (Math.random() - 0.5) * 0.1;

        if (p.x < -200) p.x = canvas.width + 200;
        if (p.x > canvas.width + 200) p.x = -200;
        if (p.y < -200) p.y = canvas.height + 200;
        if (p.y > canvas.height + 200) p.y = -200;

        ctx.beginPath();
        const grad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, dynamicRadius);
        // Ensure alpha doesn't blow out completely
        let finalAlpha = Math.min(dynamicAlpha, 0.8);
        grad.addColorStop(0, `rgba(255, 120, 0, \${finalAlpha})`); // vibrant orange
        grad.addColorStop(1, 'rgba(255, 120, 0, 0)');
        ctx.fillStyle = grad;
        ctx.arc(p.x, p.y, dynamicRadius, 0, Math.PI * 2);
        ctx.fill();
    }
    ctx.globalCompositeOperation = 'source-over';
    reqAnimFrame = requestAnimationFrame(renderCanvas);
}
renderCanvas();


// ── API INTEGRATION & FORM ──
const form = document.getElementById('scoring-form');
const submitBtn = document.getElementById('submit-btn');
const loader = document.getElementById('loader');

let lastResult = null;

form.addEventListener('submit', async (e) => {
    e.preventDefault();

    submitBtn.style.display = 'none';
    loader.style.display = 'block';

    const requestData = {
        age: parseInt(document.getElementById('age').value, 10),
        monthly_income: parseFloat(document.getElementById('monthly_income').value),
        employment_years: parseFloat(document.getElementById('employment_years').value),
        loan_amount: parseFloat(document.getElementById('loan_amount').value),
        loan_term_months: parseInt(document.getElementById('loan_term_months').value, 10),
        interest_rate: parseFloat(document.getElementById('interest_rate').value),
        past_due_30d: parseInt(document.getElementById('past_due_30d').value, 10),
        inquiries_6m: parseInt(document.getElementById('inquiries_6m').value, 10)
    };

    try {
        const response = await fetch('http://localhost:8000/api/v1/scoring/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail ? JSON.stringify(err.detail) : 'Server Error');
        }

        lastResult = await response.json();
        
        // Setup Result Page
        setupResultPage(lastResult);
        
        // Setup AI Chat
        setupChat(lastResult);
        
        showView('view-result');
    } catch (error) {
        alert('Ошибка при выполнении скоринга:\n' + error.message);
    } finally {
        submitBtn.style.display = 'block';
        loader.style.display = 'none';
    }
});


// ── SPEEDOMETER RENDER ──
function setupResultPage(data) {
    document.getElementById('res-score').textContent = data.credit_score;
    document.getElementById('res-risk-label').textContent = data.risk_segment.label.toUpperCase() + ' (' + data.risk_segment.description + ')';
    document.getElementById('res-risk-label').style.color = data.risk_segment.color;
    document.getElementById('res-probability').textContent = 'Вероятность дефолта: ' + (data.probability_of_default * 100).toFixed(2) + '%';
    
    drawSpeedometer(data.probability_of_default, data.risk_segment.color);
}

function drawSpeedometer(probability, activeHexColor) {
    const scCanvas = document.getElementById('speedometer-canvas');
    const sctx = scCanvas.getContext('2d');
    
    // Clear
    sctx.clearRect(0, 0, scCanvas.width, scCanvas.height);
    
    const centerX = scCanvas.width / 2;
    const centerY = scCanvas.height;
    const radius = 120;
    const lineWidth = 24;
    
    // Background arc (grey)
    sctx.beginPath();
    sctx.arc(centerX, centerY, radius, Math.PI, 0);
    sctx.lineWidth = lineWidth;
    sctx.lineCap = 'round';
    sctx.strokeStyle = 'rgba(255,255,255,0.08)';
    sctx.stroke();
    
    // Active arc
    sctx.beginPath();
    // Angle from PI to (PI + sweep)
    // probability 0 = full right (no default). wait: probability 0 default = very good. probability 1 = very bad.
    // Let's sweep from left (PI) up to Math.PI + (probability * Math.PI)
    const endAngle = Math.PI + (probability * Math.PI);
    sctx.arc(centerX, centerY, radius, Math.PI, endAngle);
    sctx.lineWidth = lineWidth;
    sctx.lineCap = 'round';
    sctx.strokeStyle = activeHexColor;
    sctx.stroke();
}


// ── AI CHAT LOGIC ──
const chatHistory = document.getElementById('chat-history');
const chatInput = document.getElementById('chat-input');

function appendMessage(role, text) {
    const div = document.createElement('div');
    div.classList.add('chat-bubble');
    if (role === 'ai') {
        div.classList.add('chat-ai');
    } else {
        div.classList.add('chat-user');
    }
    div.innerText = text;
    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function setupChat(data) {
    chatHistory.innerHTML = '';
    
    const shap = data.shap_values.feature_contributions;
    const entries = Object.keys(shap).map(k => ({key: k, val: shap[k]}));
    entries.sort((a,b) => Math.abs(b.val) - Math.abs(a.val));
    
    const largestContributor = entries[0];
    let msg = `Привет! Я ИИ-аналитик RizzChecker. \n\nМы проанализировали ваши параметры. Оценка вероятности дефолта \${(data.probability_of_default * 100).toFixed(1)}%. \n\nСамое сильное влияние оказал параметр '\${largestContributor.key}'. Чем я могу помочь в планировании улучшения вашего скоринга?`;
    
    appendMessage('ai', msg);
}

function sendChatMessage() {
    const text = chatInput.value.trim();
    if (!text) return;
    
    appendMessage('user', text);
    chatInput.value = '';
    
    // Fake typing reply
    setTimeout(() => {
        appendMessage('ai', 'Анализируя ваши данные, я рекомендую сфокусироваться на стабильности доходов и избегать новых запросов кредитной истории в ближайшие полгода. Это значительно снизит уровень риска модели.');
    }, 1500);
}

function handleChatEnter(e) {
    if (e.key === 'Enter') {
        sendChatMessage();
    }
}

// ── CALCULATOR LOGIC ──
function calculateCalc() {
    const amt = parseFloat(document.getElementById('calc_amount').value) || 0;
    const term = Math.max(1, parseInt(document.getElementById('calc_term').value, 10) || 1);
    const rate = parseFloat(document.getElementById('calc_rate').value) || 0;
    
    // standard annuity formula: M = P * (r*(1+r)^n) / ((1+r)^n - 1)
    const r = (rate / 100) / 12;
    let payment = 0;
    if (r > 0) {
        payment = amt * (r * Math.pow(1 + r, term)) / (Math.pow(1 + r, term) - 1);
    } else {
        payment = amt / term;
    }
    
    const fmt = Math.round(payment).toLocaleString('ru-RU');
    document.getElementById('calc-monthly-payment').textContent = fmt + ' ₽';
}
