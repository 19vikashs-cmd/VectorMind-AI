let chartInstance = null;

let selAlgo = 'hnsw';

let vectorPoints = [];

let animationRunning = false;

// ======================================
// CATEGORY COLORS
// ======================================

const CATEGORY_COLORS = {

    cs: '#6c63ff',

    math: '#00d9ff',

    food: '#00ff88',

    sports: '#ffcc00',

    general: '#ffffff'
};

// ======================================
// TAB SWITCH
// ======================================

function switchTab(name, el) {

    document
        .querySelectorAll('.tab')
        .forEach(tab => {

            tab.classList.remove('on');
        });

    document
        .querySelectorAll('.tab-content')
        .forEach(tab => {

            tab.classList.remove('on');
        });

    el.classList.add('on');

    document
        .getElementById(`tab-${name}`)
        .classList.add('on');
}

// ======================================
// SET ALGORITHM
// ======================================

function setAlgo(el) {

    document
        .querySelectorAll('.algo-btn')
        .forEach(btn => {

            btn.classList.remove('on');
        });

    el.classList.add('on');

    selAlgo = el.dataset.algo;
}

// ======================================
// LOAD STATUS
// ======================================

async function loadStatus() {

    try {

        const response =
            await fetch('/status');

        const data =
            await response.json();

        document
            .getElementById('statusBox')
            .innerHTML = `

                <b>Status:</b> ${data.status}<br><br>

                <b>Ollama:</b> ${data.ollama}<br><br>

                <b>Vectors:</b> ${data.vector_count}<br><br>

                <b>Documents:</b> ${data.document_count}
            `;

        document
            .getElementById('statsLabel')
            .innerText =
            `${data.vector_count} vectors loaded`;

        document
            .getElementById('ollamaBadge')
            .innerText =
            data.ollama;

    } catch (error) {

        console.error(error);
    }
}

// ======================================
// LOAD PCA DATA
// ======================================

async function loadVectorVisualization() {

    try {

        const response =
            await fetch('/pca');

        const items =
            await response.json();

        if (!Array.isArray(items)) {

            console.error('Invalid PCA response');

            return;
        }

        if (items.length === 0) {

            vectorPoints = [];

            return;
        }

        // ======================================
        // ADD GENERAL CLUSTER
        // ======================================

        for (let i = 0; i < 40; i++) {

            items.push({

                x: 15 + Math.random() * 2,

                y: -15 + Math.random() * 2,

                category: 'general',

                metadata: `general-${i}`
            });
        }

        // ======================================
        // NORMALIZE
        // ======================================

        const xs = items.map(p => p.x);

        const ys = items.map(p => p.y);

        const minX = Math.min(...xs);

        const maxX = Math.max(...xs);

        const minY = Math.min(...ys);

        const maxY = Math.max(...ys);

        const padding = 0.12;

vectorPoints = items.map(item => ({

    x:
        padding +
        (
            (item.x - minX)
            /
            ((maxX - minX) || 1)
        ) * (1 - padding * 2),

    y:
        padding +
        (
            (item.y - minY)
            /
            ((maxY - minY) || 1)
        ) * (1 - padding * 2),

            category:
                item.category || 'general',

            metadata:
                item.metadata || '',

            highlight: false,

            // movement restored
            vx:
                (Math.random() - 0.5) * 0.0012,

            vy:
                (Math.random() - 0.5) * 0.0012,

            // blinking
            pulse: Math.random(),

            pulseDirection: 1
        }));

        if (!animationRunning) {

            animateVisualization();
        }

    } catch (error) {

        console.error(error);
    }
}

// ======================================
// ANIMATION
// ======================================

function animateVisualization() {

    const canvas =
        document.getElementById('scatter');

    if (!canvas) return;

    const ctx =
        canvas.getContext('2d');

    animationRunning = true;

    function render() {

        canvas.width =
            canvas.parentElement.clientWidth;

        canvas.height =
            canvas.parentElement.clientHeight;

        // ======================================
        // BACKGROUND
        // ======================================

        ctx.fillStyle = '#07070f';

        ctx.fillRect(
            0,
            0,
            canvas.width,
            canvas.height
        );

        // ======================================
        // GRID
        // ======================================

        ctx.strokeStyle =
            'rgba(255,255,255,0.04)';

        for (let i = 0; i < canvas.width; i += 80) {

            ctx.beginPath();

            ctx.moveTo(i, 0);

            ctx.lineTo(i, canvas.height);

            ctx.stroke();
        }

        for (let i = 0; i < canvas.height; i += 80) {

            ctx.beginPath();

            ctx.moveTo(0, i);

            ctx.lineTo(canvas.width, i);

            ctx.stroke();
        }

        // ======================================
        // CONNECTIONS
        // ======================================

        for (let i = 0; i < vectorPoints.length; i++) {

            const a = vectorPoints[i];

            for (let j = i + 1; j < vectorPoints.length; j++) {

                const b = vectorPoints[j];

                const dx = a.x - b.x;

                const dy = a.y - b.y;

                const dist =
                    Math.sqrt(dx * dx + dy * dy);

                if (
                    dist < 0.08
                    &&
                    a.category === b.category
                ) {

                    ctx.beginPath();

                    ctx.moveTo(
                        a.x * canvas.width,
                        a.y * canvas.height
                    );

                    ctx.lineTo(
                        b.x * canvas.width,
                        b.y * canvas.height
                    );

                    ctx.strokeStyle =
                        a.highlight || b.highlight
                            ? 'rgba(255,255,255,0.22)'
                            : 'rgba(255,255,255,0.035)';

                    ctx.stroke();
                }
            }
        }

        // ======================================
        // DRAW POINTS
        // ======================================

        vectorPoints.forEach(point => {

            // ======================================
            // MOVEMENT
            // ======================================

            point.x += point.vx;

            point.y += point.vy;

            if (point.x <= 0.02 || point.x >= 0.98) {

                point.vx *= -1;
            }

            if (point.y <= 0.02 || point.y >= 0.98) {

                point.vy *= -1;
            }

            // ======================================
            // PULSE
            // ======================================

            if (point.highlight) {

                point.pulse +=
                    0.025 * point.pulseDirection;

                if (point.pulse >= 1) {

                    point.pulseDirection = -1;
                }

                if (point.pulse <= 0) {

                    point.pulseDirection = 1;
                }

            } else {

                point.pulse = 0.2;
            }

            const px =
                point.x * canvas.width;

            const py =
                point.y * canvas.height;

            const color =
                CATEGORY_COLORS[
                    point.category
                ]
                ||
                '#ffffff';

            const glowSize =
                point.highlight
                    ? 18 + (point.pulse * 16)
                    : 10;

            const radius =
                point.highlight
                    ? 5 + (point.pulse * 3)
                    : 3;

            // ======================================
            // GLOW
            // ======================================

            const gradient =
                ctx.createRadialGradient(
                    px,
                    py,
                    1,
                    px,
                    py,
                    glowSize
                );

            gradient.addColorStop(0, color);

            gradient.addColorStop(
                1,
                'transparent'
            );

            ctx.beginPath();

            ctx.arc(
                px,
                py,
                glowSize,
                0,
                Math.PI * 2
            );

            ctx.fillStyle = gradient;

            ctx.fill();

            // ======================================
            // MAIN DOT
            // ======================================

            ctx.beginPath();

            ctx.arc(
                px,
                py,
                radius,
                0,
                Math.PI * 2
            );

            ctx.fillStyle = color;

            ctx.shadowBlur =
                point.highlight ? 40 : 12;

            ctx.shadowColor = color;

            ctx.fill();

            ctx.shadowBlur = 0;
        });

        // ======================================
        // LABELS
        // ======================================

        ctx.fillStyle =
            'rgba(255,255,255,0.45)';

        ctx.font = '12px Arial';

        ctx.fillText(
            'AI / CS',
            40,
            40
        );

        ctx.fillText(
            'FOOD',
            canvas.width - 100,
            60
        );

        ctx.fillText(
            'SPORTS',
            60,
            canvas.height - 40
        );

        ctx.fillText(
            'MATH',
            canvas.width - 100,
            canvas.height - 40
        );

        ctx.fillText(
            'GENERAL',
            canvas.width / 2 - 40,
            canvas.height / 2
        );

        requestAnimationFrame(render);
    }

    render();
}

// ======================================
// SEARCH
// ======================================

async function runSearch() {

    const text =
        document
            .getElementById('qInput')
            .value
            .trim();

    if (!text) return;

    const metric =
        document
            .getElementById('metric')
            .value;

    const k =
        document
            .getElementById('kSlider')
            .value;

    const resultsDiv =
        document.getElementById('results');

    resultsDiv.innerHTML =
        `<div class="rcard">Searching...</div>`;

    try {

        const response =
            await fetch(
                `/search?q=${encodeURIComponent(text)}&algo=${selAlgo}&metric=${metric}&k=${k}`
            );

        const data =
            await response.json();

        // RESET

        vectorPoints.forEach(point => {

            point.highlight = false;
        });

        // HIGHLIGHT RESULTS

        if (data.results) {

            const matchedMetadata =
                data.results.map(
                    r => (r.metadata || '').toLowerCase()
                );

            vectorPoints.forEach(point => {

                const meta =
                    (point.metadata || '').toLowerCase();

                if (
                    matchedMetadata.some(
                        m => meta.includes(m)
                    )
                ) {

                    point.highlight = true;
                }
            });
        }

        // LATENCY

        document
            .getElementById('latBig')
            .innerText =
            `${((data.latencyUs || 0) / 1000).toFixed(2)} ms`;

        document
            .getElementById('latSub')
            .innerText =
            `${selAlgo.toUpperCase()} • ${metric}`;

        // RESULTS

        resultsDiv.innerHTML = '';

        if (
            !data.results
            ||
            data.results.length === 0
        ) {

            resultsDiv.innerHTML = `

                <div class="rcard">
                    No results found
                </div>
            `;

            return;
        }

        data.results.forEach(item => {

            const score =
                ((item.score || 0) * 100)
                .toFixed(1);

            resultsDiv.innerHTML += `

                <div class="rcard">

                    <div style="
                        display:flex;
                        justify-content:space-between;
                        margin-bottom:10px;
                    ">

                        <b>${item.category}</b>

                        <span style="
                            color:#00d9ff;
                        ">
                            ${score}% match
                        </span>

                    </div>

                    <div>
                        ${item.metadata}
                    </div>

                </div>
            `;
        });

    } catch (error) {

        console.error(error);

        resultsDiv.innerHTML = `

            <div class="rcard">
                Search failed
            </div>
        `;
    }
}

// ======================================
// ASK AI
// ======================================

async function askAI() {

    const input =
        document.getElementById('ragQuestion');

    const question =
        input.value.trim();

    if (!question) return;

    const history =
        document.getElementById('chatHistory');

    history.innerHTML += `

        <div class="chat-q">
            ${question}
        </div>
    `;

    input.value = '';

    history.innerHTML += `

        <div class="chat-a" id="thinking">
            Thinking...
        </div>
    `;

    history.scrollTop =
        history.scrollHeight;

    try {

        const response =
            await fetch('/chat', {

                method: 'POST',

                headers: {
                    'Content-Type': 'application/json'
                },

                body: JSON.stringify({
                    message: question
                })
            });

        const data =
            await response.json();

        // RESET

        vectorPoints.forEach(point => {

            point.highlight = false;
        });

        // ======================================
        // HIGHLIGHT RAG MATCHES
        // ======================================

        if (data.matches) {

            const allTexts = [];

            data.matches.forEach(match => {

                if (match.metadata) {

                    allTexts.push(
                        match.metadata.toLowerCase()
                    );
                }

                if (match.document?.text) {

                    allTexts.push(
                        match.document.text
                            .substring(0, 80)
                            .toLowerCase()
                    );
                }
            });

            vectorPoints.forEach(point => {

                const meta =
                    (point.metadata || '').toLowerCase();

                if (
                    allTexts.some(
                        t =>
                            t &&
                            (
                                meta.includes(t)
                                ||
                                t.includes(meta)
                            )
                    )
                ) {

                    point.highlight = true;
                }
            });
        }

        const thinking =
            document.getElementById('thinking');

        if (thinking) {

            thinking.remove();
        }

        let finalResponse = '';

        if (data.response) {

            finalResponse = data.response;

        } else if (data.error) {

            finalResponse =
                `❌ Error: ${data.error}`;

        } else {

            finalResponse =
                '❌ No response from model';
        }

        history.innerHTML += `

            <div class="chat-a">
                ${finalResponse}
            </div>
        `;

        history.scrollTop =
            history.scrollHeight;

    } catch (error) {

        console.error(error);

        const thinking =
            document.getElementById('thinking');

        if (thinking) {

            thinking.remove();
        }

        history.innerHTML += `

            <div class="chat-a">
                ❌ Failed to connect to backend
            </div>
        `;
    }
}

// ======================================
// BENCHMARK
// ======================================

async function runBenchmark() {

    try {

        const response =
            await fetch('/benchmark');

        const data =
            await response.json();

        renderBenchmark(data);

    } catch (error) {

        console.error(error);
    }
}

// ======================================
// RENDER BENCHMARK
// ======================================

function renderBenchmark(data) {

    document
        .getElementById('benchBars')
        .innerHTML = `

            <div class="rcard">
                HNSW:
                ${data.hnsw.time_ms} ms
            </div>

            <div class="rcard">
                KDTree:
                ${data.kdtree.time_ms} ms
            </div>

            <div class="rcard">
                Bruteforce:
                ${data.bruteforce.time_ms} ms
            </div>
        `;
}

// ======================================
// INSERT VECTOR
// ======================================

async function addVector() {

    const meta =
        document
            .getElementById('addMeta')
            .value
            .trim();

    const cat =
        document
            .getElementById('addCat')
            .value;

    if (!meta) {

        alert('Please enter vector text');

        return;
    }

    try {

        const response =
            await fetch('/insert-vector', {

                method: 'POST',

                headers: {
                    'Content-Type': 'application/json'
                },

                body: JSON.stringify({

                    metadata: meta,

                    category: cat
                })
            });

        const data =
            await response.json();

        if (data.success) {

            alert('✅ Vector inserted successfully');

            document
                .getElementById('addMeta')
                .value = '';

            await loadStatus();

            await loadVectorVisualization();

        } else {

            alert(
                `❌ ${data.error || 'Insert failed'}`
            );
        }

    } catch (error) {

        console.error(error);

        alert('❌ Server error');
    }
}

// ======================================
// INSERT DOCUMENT
// ======================================

async function insertDocument() {

    const title =
        document
            .getElementById('docTitle')
            .value
            .trim();

    const text =
        document
            .getElementById('docText')
            .value
            .trim();

    if (!title || !text) {

        alert('Missing fields');

        return;
    }

    try {

        const response =
            await fetch('/doc/insert', {

                method: 'POST',

                headers: {
                    'Content-Type': 'application/json'
                },

                body: JSON.stringify({
                    title,
                    text
                })
            });

        const data =
            await response.json();

        if (data.success) {

            alert('✅ Document inserted');

            document
                .getElementById('docTitle')
                .value = '';

            document
                .getElementById('docText')
                .value = '';

            await loadStatus();

        } else {

            alert(
                `❌ ${data.error || 'Insert failed'}`
            );
        }

    } catch (error) {

        console.error(error);

        alert('❌ Failed to insert document');
    }
}

// ======================================
// ENTER SUPPORT
// ======================================

document.addEventListener('DOMContentLoaded', () => {

    const qInput =
        document.getElementById('qInput');

    if (qInput) {

        qInput.addEventListener('keypress', async e => {

            if (e.key === 'Enter') {

                await runSearch();
            }
        });
    }

    const rag =
        document.getElementById('ragQuestion');

    if (rag) {

        rag.addEventListener('keypress', async e => {

            if (
                e.key === 'Enter'
                &&
                !e.shiftKey
            ) {

                e.preventDefault();

                await askAI();
            }
        });
    }
});

// ======================================
// INIT
// ======================================

window.onload = async () => {

    await loadStatus();

    await loadVectorVisualization();

    await runBenchmark();
};