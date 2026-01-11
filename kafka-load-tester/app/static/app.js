// WebSocket connection
let ws = null;
let reconnectInterval = null;

// DOM elements
const form = document.getElementById('load-test-form');
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const connectionStatus = document.getElementById('connection-status');
const logDisplay = document.getElementById('log-display');

// Status display elements
const statusRunning = document.getElementById('status-running');
const statusTestId = document.getElementById('status-test-id');
const statusSent = document.getElementById('status-sent');
const statusFailed = document.getElementById('status-failed');
const statusRate = document.getElementById('status-rate');
const statusElapsed = document.getElementById('status-elapsed');
const statusProgress = document.getElementById('status-progress');
const progressFill = document.getElementById('progress-fill');

// Form input elements
const messageCountInput = document.getElementById('message-count');
const messageRateInput = document.getElementById('message-rate');
const topicInput = document.getElementById('topic');
const payloadSizeInput = document.getElementById('payload-size');
const testNameInput = document.getElementById('test-name');

// Connect to WebSocket
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/status`;

    log('Connecting to server...', 'info');

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        log('Connected to server', 'success');
        connectionStatus.textContent = 'Connected';
        connectionStatus.className = 'status-badge connected';

        if (reconnectInterval) {
            clearInterval(reconnectInterval);
            reconnectInterval = null;
        }
    };

    ws.onmessage = (event) => {
        const status = JSON.parse(event.data);
        updateStatus(status);
    };

    ws.onerror = (error) => {
        log('WebSocket error occurred', 'error');
    };

    ws.onclose = () => {
        log('Disconnected from server', 'warning');
        connectionStatus.textContent = 'Disconnected';
        connectionStatus.className = 'status-badge disconnected';

        // Attempt to reconnect
        if (!reconnectInterval) {
            reconnectInterval = setInterval(() => {
                log('Attempting to reconnect...', 'info');
                connectWebSocket();
            }, 5000);
        }
    };
}

// Update status display
function updateStatus(status) {
    statusRunning.textContent = status.running ? 'Yes' : 'No';
    statusRunning.style.color = status.running ? 'var(--success-color)' : 'var(--text-primary)';

    statusTestId.textContent = status.test_id || '-';
    statusSent.textContent = status.messages_sent.toLocaleString();
    statusFailed.textContent = status.messages_failed.toLocaleString();

    if (status.messages_failed > 0) {
        statusFailed.style.color = 'var(--danger-color)';
    } else {
        statusFailed.style.color = 'var(--text-primary)';
    }

    statusRate.textContent = `${status.current_rate.toFixed(2)} msg/s`;
    statusElapsed.textContent = `${status.elapsed_seconds.toFixed(2)}s`;
    statusProgress.textContent = `${status.progress_percent.toFixed(1)}%`;

    progressFill.style.width = `${status.progress_percent}%`;

    // Update button states
    if (status.running) {
        startBtn.disabled = true;
        stopBtn.disabled = false;
        disableForm();
    } else {
        startBtn.disabled = false;
        stopBtn.disabled = true;
        enableForm();
    }
}

// Start load test
async function startLoadTest(event) {
    event.preventDefault();

    const config = {
        message_count: parseInt(messageCountInput.value),
        message_rate: parseInt(messageRateInput.value),
        topic: topicInput.value,
        payload_size: parseInt(payloadSizeInput.value),
        test_name: testNameInput.value || null
    };

    log(`Starting load test: ${config.message_count} messages @ ${config.message_rate}/s to topic "${config.topic}"`, 'info');

    try {
        const response = await fetch('/api/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });

        const result = await response.json();

        if (response.ok) {
            log('Load test started successfully', 'success');
        } else {
            log(`Failed to start test: ${result.detail}`, 'error');
        }
    } catch (error) {
        log(`Error starting test: ${error.message}`, 'error');
    }
}

// Stop load test
async function stopLoadTest() {
    log('Requesting test stop...', 'warning');

    try {
        const response = await fetch('/api/stop', {
            method: 'POST'
        });

        const result = await response.json();

        if (response.ok) {
            log('Test stop requested', 'warning');
        } else {
            log(`Failed to stop test: ${result.detail}`, 'error');
        }
    } catch (error) {
        log(`Error stopping test: ${error.message}`, 'error');
    }
}

// Logging function
function log(message, level = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.className = `log-entry ${level}`;
    entry.innerHTML = `<span class="timestamp">[${timestamp}]</span> ${message}`;

    logDisplay.appendChild(entry);
    logDisplay.scrollTop = logDisplay.scrollHeight;

    // Keep only last 100 entries
    while (logDisplay.children.length > 100) {
        logDisplay.removeChild(logDisplay.firstChild);
    }
}

// Form controls
function disableForm() {
    messageCountInput.disabled = true;
    messageRateInput.disabled = true;
    topicInput.disabled = true;
    payloadSizeInput.disabled = true;
    testNameInput.disabled = true;
}

function enableForm() {
    messageCountInput.disabled = false;
    messageRateInput.disabled = false;
    topicInput.disabled = false;
    payloadSizeInput.disabled = false;
    testNameInput.disabled = false;
}

// Preset buttons
document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const count = btn.dataset.count;
        const rate = btn.dataset.rate;

        messageCountInput.value = count;
        messageRateInput.value = rate;

        log(`Applied preset: ${parseInt(count).toLocaleString()} messages @ ${parseInt(rate).toLocaleString()}/s`, 'info');
    });
});

// Event listeners
form.addEventListener('submit', startLoadTest);
stopBtn.addEventListener('click', stopLoadTest);

// Initialize
connectWebSocket();
log('Kafka Load Tester initialized', 'info');