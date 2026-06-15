document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const htmlEl = document.documentElement;

    // --- Interactive Aurora Mesh Gradients & Cyber Grid Background ---
    let canvasAnimId = null;
    function initParticles(theme) {
        if (canvasAnimId) {
            cancelAnimationFrame(canvasAnimId);
        }

        const container = document.getElementById('particles-js');
        if (!container) return;
        container.innerHTML = ''; 

        const canvas = document.createElement('canvas');
        canvas.style.position = 'absolute';
        canvas.style.top = '0';
        canvas.style.left = '0';
        canvas.style.width = '100%';
        canvas.style.height = '100%';
        canvas.style.display = 'block';
        container.appendChild(canvas);

        const ctx = canvas.getContext('2d');
        let width = canvas.width = container.offsetWidth;
        let height = canvas.height = container.offsetHeight;

        function handleResize() {
            if (!container) return;
            width = canvas.width = container.offsetWidth;
            height = canvas.height = container.offsetHeight;
        }
        window.removeEventListener('resize', handleResize);
        window.addEventListener('resize', handleResize);

        const isLight = theme === 'light';

        // Interactive mouse spring physics for the glowing follower orb
        const mouse = { x: width / 2, y: height / 2, active: false };
        function handleMouseMove(e) {
            const rect = canvas.getBoundingClientRect();
            mouse.x = e.clientX - rect.left;
            mouse.y = e.clientY - rect.top;
            mouse.active = true;
        }
        function handleMouseLeave() {
            mouse.active = false;
        }
        window.removeEventListener('mousemove', handleMouseMove);
        window.addEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseleave', handleMouseLeave);
        window.addEventListener('mouseleave', handleMouseLeave);

        // Generate slow-moving organic liquid light orbs (Mesh Gradients)
        const orbs = [
            {
                x: width * 0.3,
                y: height * 0.4,
                vx: 0.18,
                vy: -0.15,
                radius: Math.min(width, height) * 0.45,
                color: isLight ? 'rgba(37, 99, 235, 0.08)' : 'rgba(0, 240, 255, 0.09)' // Electric Cyan
            },
            {
                x: width * 0.7,
                y: height * 0.3,
                vx: -0.12,
                vy: 0.2,
                radius: Math.min(width, height) * 0.55,
                color: isLight ? 'rgba(139, 92, 246, 0.07)' : 'rgba(123, 44, 191, 0.1)' // Royal Indigo
            },
            {
                x: width * 0.4,
                y: height * 0.8,
                vx: 0.15,
                vy: 0.12,
                radius: Math.min(width, height) * 0.5,
                color: isLight ? 'rgba(16, 185, 129, 0.06)' : 'rgba(57, 255, 20, 0.06)' // Neon Mint
            },
            {
                x: width * 0.8,
                y: height * 0.7,
                vx: -0.15,
                vy: -0.18,
                radius: Math.min(width, height) * 0.4,
                color: isLight ? 'rgba(244, 63, 94, 0.05)' : 'rgba(255, 0, 60, 0.05)' // Neon Rose
            }
        ];

        // Generate a subtle count of soft, blurry fading light particles (animated dots)
        const dots = [];
        const dotCount = 70; // increased to 70 for a spectacular interactive neural swarm constellation
        const dotColors = isLight
            ? ['rgba(37, 99, 235, ALPHA)', 'rgba(139, 92, 246, ALPHA)', 'rgba(16, 185, 129, ALPHA)']
            : ['rgba(0, 240, 255, ALPHA)', 'rgba(57, 255, 20, ALPHA)', 'rgba(255, 0, 90, ALPHA)'];

        for (let i = 0; i < dotCount; i++) {
            dots.push({
                x: Math.random() * width,
                y: Math.random() * height,
                vx: (Math.random() - 0.5) * 0.18, // extremely slow drifting
                vy: (Math.random() - 0.5) * 0.18,
                radius: Math.random() * 6 + 4, // medium-sized for blurry aura
                color: dotColors[Math.floor(Math.random() * dotColors.length)],
                phase: Math.random() * Math.PI * 2, // dynamic fade offset
                fadeSpeed: 0.008 + Math.random() * 0.012
            });
        }

        function draw() {
            // Smooth background base
            ctx.fillStyle = isLight ? '#f4f6fa' : '#040406';
            ctx.fillRect(0, 0, width, height);

            // Draw organic shifting mesh gradients
            orbs.forEach((orb, index) => {
                // Update position
                orb.x += orb.vx;
                orb.y += orb.vy;

                // Screen boundary smooth bounces
                if (orb.x < -orb.radius || orb.x > width + orb.radius) orb.vx *= -1;
                if (orb.y < -orb.radius || orb.y > height + orb.radius) orb.vy *= -1;

                // Smoothly attract Orb 1 to the mouse coordinates if mouse is active
                if (index === 0 && mouse.active) {
                    orb.x += (mouse.x - orb.x) * 0.08;
                    orb.y += (mouse.y - orb.y) * 0.08;
                }

                // Render soft radial mesh gradient
                const grad = ctx.createRadialGradient(orb.x, orb.y, 0, orb.x, orb.y, orb.radius);
                grad.addColorStop(0, orb.color);
                grad.addColorStop(1, 'transparent');

                ctx.fillStyle = grad;
                ctx.beginPath();
                ctx.arc(orb.x, orb.y, orb.radius, 0, Math.PI * 2);
                ctx.fill();
            });

            // Draw extremely subtle cyber grid overlay
            ctx.strokeStyle = isLight ? 'rgba(37, 99, 235, 0.025)' : 'rgba(255, 255, 255, 0.012)';
            ctx.lineWidth = 1;
            const gridSpacing = 65;

            // Vertical grid lanes
            for (let x = 0; x < width; x += gridSpacing) {
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, height);
                ctx.stroke();
            }

            // Horizontal grid lanes
            for (let y = 0; y < height; y += gridSpacing) {
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(width, y);
                ctx.stroke();
            }

            // Draw organic glowing thread links between close drifting fireflies
            ctx.lineWidth = 0.7;
            for (let i = 0; i < dots.length; i++) {
                for (let j = i + 1; j < dots.length; j++) {
                    const d1 = dots[i];
                    const d2 = dots[j];
                    const dist = Math.hypot(d1.x - d2.x, d1.y - d2.y);
                    
                    if (dist < 95) {
                        // Calculate alphas and combine them for smooth breathing fade
                        const alpha1 = (Math.sin(d1.phase) + 1) * 0.5;
                        const alpha2 = (Math.sin(d2.phase) + 1) * 0.5;
                        const proximityAlpha = (1 - (dist / 95)) * alpha1 * alpha2 * (isLight ? 0.09 : 0.18);
                        
                        ctx.strokeStyle = isLight 
                            ? `rgba(37, 99, 235, ${proximityAlpha})`
                            : `rgba(0, 240, 255, ${proximityAlpha})`;
                        ctx.beginPath();
                        ctx.moveTo(d1.x, d1.y);
                        ctx.lineTo(d2.x, d2.y);
                        ctx.stroke();
                    }
                }
            }

            // Draw the soft blurry fading animated dots with mouse gravity swarming
            dots.forEach(dot => {
                // Smooth gravitational attraction towards the cursor
                if (mouse.active) {
                    const dx = mouse.x - dot.x;
                    const dy = mouse.y - dot.y;
                    const dist = Math.hypot(dx, dy);
                    if (dist < 260) {
                        const gravityFactor = (260 - dist) / 260;
                        dot.vx += (dx / dist) * gravityFactor * 0.024;
                        dot.vy += (dy / dist) * gravityFactor * 0.024;
                    }
                }

                // Speed limit damping to preserve slow-motion luxury drift
                const speed = Math.hypot(dot.vx, dot.vy);
                const maxSpeed = 0.55;
                if (speed > maxSpeed) {
                    dot.vx = (dot.vx / speed) * maxSpeed;
                    dot.vy = (dot.vy / speed) * maxSpeed;
                }
                
                // Slow friction damping
                dot.vx *= 0.985;
                dot.vy *= 0.985;

                dot.x += dot.vx;
                dot.y += dot.vy;

                // Screen wrap-around bounds checking
                if (dot.x < -20) dot.x = width + 20;
                if (dot.x > width + 20) dot.x = -20;
                if (dot.y < -20) dot.y = height + 20;
                if (dot.y > height + 20) dot.y = -20;

                // Breathing alpha oscillation
                dot.phase += dot.fadeSpeed;
                const activeAlpha = (Math.sin(dot.phase) + 1) * 0.5 * (isLight ? 0.22 : 0.38) + 0.02;

                // Render soft glowing blurry firefly dot
                const dotGrad = ctx.createRadialGradient(dot.x, dot.y, 0, dot.x, dot.y, dot.radius);
                const rgbString = dot.color.replace('ALPHA', activeAlpha);
                dotGrad.addColorStop(0, rgbString);
                dotGrad.addColorStop(0.3, dot.color.replace('ALPHA', activeAlpha * 0.4));
                dotGrad.addColorStop(1, 'transparent');

                ctx.fillStyle = dotGrad;
                ctx.beginPath();
                ctx.arc(dot.x, dot.y, dot.radius * 2.2, 0, Math.PI * 2);
                ctx.fill();

                // Render high-intensity glowing central core
                ctx.beginPath();
                ctx.arc(dot.x, dot.y, 1.2, 0, Math.PI * 2);
                ctx.fillStyle = isLight 
                    ? `rgba(37, 99, 235, ${activeAlpha * 1.5})`
                    : `rgba(255, 255, 255, ${activeAlpha * 2.0})`;
                ctx.fill();
            });

            canvasAnimId = requestAnimationFrame(draw);
        }

        draw();
    }

    initParticles(htmlEl.getAttribute('data-theme'));

    themeToggle.addEventListener('click', () => {
        const currentTheme = htmlEl.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        htmlEl.setAttribute('data-theme', newTheme);
        renderCharts();
        initParticles(newTheme);
    });

    // --- DOM Elements ---
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const uploadPreview = document.getElementById('upload-preview');
    const previewVideo = document.getElementById('preview-video');
    const startBtn = document.getElementById('start-btn');
    
    const processingSection = document.getElementById('processing-section');
    const progressBar = document.getElementById('progress-bar');
    const progressStatus = document.getElementById('progress-status');
    
    const resultsSection = document.getElementById('results-section');
    const valFrames = document.getElementById('val-frames');
    const valAvg = document.getElementById('val-avg');
    const valMax = document.getElementById('val-max');
    const valLevel = document.getElementById('val-level');
    const outputVideo = document.getElementById('output-video');
    
    const btnGenerateReport = document.getElementById('generate-report');
    const btnSendReport = document.getElementById('send-report');
    const reportStatus = document.getElementById('report-status');

    let globalResults = null;

    // --- Drag & Drop Upload ---
    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
    dropZone.addEventListener('dragleave', () => { dropZone.classList.remove('dragover'); });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            handleFileUpload();
        }
    });
    fileInput.addEventListener('change', handleFileUpload);

    async function handleFileUpload() {
        if (!fileInput.files.length) return;
        const file = fileInput.files[0];
        
        dropZone.innerHTML = `<div class="drop-content"><p class="primary-text" style="color:var(--warning)">[ UPLOADING... ]</p><p class="secondary-text">${file.name}</p></div>`;
        
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/upload', { method: 'POST', body: formData });
            const data = await response.json();
            
            if(response.ok) {
                dropZone.innerHTML = `<div class="drop-content"><p class="primary-text" style="color:var(--success)">[ VIDEO UPLOADED ]</p><p class="secondary-text">${file.name}</p></div>`;
                uploadPreview.classList.remove('hidden');
                // The backend no longer blocks to generate a preview. We load the raw video directly.
                previewVideo.src = data.preview_url + "?t=" + new Date().getTime();
                previewVideo.load();
                previewVideo.play().catch(e => console.log("Autoplay prevented:", e));
            } else {
                dropZone.innerHTML = `<div class="drop-content"><p class="primary-text" style="color:var(--danger)">[ UPLOAD FAILED ]</p><p class="secondary-text">${data.error}</p></div>`;
            }
        } catch (error) {
            dropZone.innerHTML = `<div class="drop-content"><p class="primary-text" style="color:var(--danger)">[ CONNECTION ERROR ]</p></div>`;
        }
    }

    // --- Start Analysis ---
    startBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/api/analyze', { method: 'POST' });
            if(response.ok) {
                processingSection.classList.remove('hidden');
                startBtn.classList.add('hidden');
                dropZone.classList.add('hidden'); // Hide upload to focus on processing
                
                // Start polling
                pollStatus();
            } else {
                const data = await response.json();
                alert("Error starting analysis: " + data.error);
            }
        } catch (error) {
            console.error("Failed to start analysis", error);
        }
    });

    // --- Polling Status ---
    async function pollStatus() {
        const interval = setInterval(async () => {
            try {
                // Add timestamp to prevent caching
                const response = await fetch('/api/status?_t=' + new Date().getTime());
                const data = await response.json();

                progressBar.style.width = `${data.progress}%`;
                
                // Typewriter effect logic
                if (data.message && window.lastLogMsg !== data.message) {
                    window.lastLogMsg = data.message;
                    const newLog = document.createElement('p');
                    newLog.className = "typewriter-text";
                    newLog.innerText = `> ${data.message}`;
                    progressStatus.parentElement.appendChild(newLog);
                    progressStatus.parentElement.scrollTop = progressStatus.parentElement.scrollHeight;
                }

                if (data.completed) {
                    clearInterval(interval);
                    globalResults = data.results;
                    setTimeout(showResults, 1000); // Wait 1s so user sees 100% completion
                } else if (!data.is_running && !data.completed && data.error) {
                    clearInterval(interval);
                    progressStatus.innerText = `> [ ERROR ] ${data.error}`;
                    progressStatus.style.color = "var(--danger)";
                    progressBar.style.background = "var(--danger)";
                }
            } catch (error) {
                console.error("Polling error", error);
            }
        }, 2000);
    }

    // --- Show Results ---
    function showResults() {
        resultsSection.classList.remove('hidden');

        // "Total Frames" metric shows the REAL frame count of the video file
        const realFrames      = globalResults.video_total_frames || globalResults.total_frames;
        const processedFrames = globalResults.processed_frames   || globalResults.total_frames;

        animateValue(valFrames, 0, realFrames, 1500);

        // Append a small sub-label showing how many frames were actually processed
        if (realFrames !== processedFrames) {
            const sub = document.createElement('span');
            sub.style.cssText = 'display:block;font-size:0.65em;opacity:0.6;margin-top:2px;';
            sub.textContent   = `(${processedFrames.toLocaleString()} analysed)`;
            valFrames.parentElement.appendChild(sub);
        }

        valAvg.innerText   = globalResults.avg_veh;
        animateValue(valMax, 0, globalResults.max_veh, 1500);
        valLevel.innerText = globalResults.traffic_level;

        // Output Video
        outputVideo.src = "/api/output_video?t=" + new Date().getTime();

        // Render Charts
        renderCharts();
    }

    // Number animation helper
    function animateValue(obj, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            obj.innerHTML = Math.floor(progress * (end - start) + start);
            if (progress < 1) window.requestAnimationFrame(step);
        };
        window.requestAnimationFrame(step);
    }

    // --- Charts (Plotly) ---
    function renderCharts() {
        if (!globalResults) return;

        // DEBUG: Log the raw data being rendered
        console.debug('[CHARTS] graph_data received:', JSON.stringify(globalResults.graph_data, null, 2));
        console.debug('[CHARTS] video_name:', globalResults.video_name);
        console.debug('[CHARTS] total_frames:', globalResults.total_frames);
        console.debug('[CHARTS] pred_steps:', globalResults.pred_steps);

        const isDark = htmlEl.getAttribute('data-theme') === 'dark';
        const fontColor = isDark ? '#8b9bb4' : '#64748b';
        const titleColor = isDark ? '#f8f9fa' : '#0f172a';
        const bgColor = 'transparent';
        const gridColor = isDark ? 'rgba(65, 105, 225, 0.1)' : 'rgba(0,0,0,0.05)';
        const primaryColor = isDark ? '#00f0ff' : '#2563eb';

        const layoutTemplate = {
            paper_bgcolor: bgColor, plot_bgcolor: bgColor,
            font: { color: fontColor, family: "'Outfit', sans-serif" },
            title: { font: { color: titleColor, size: 16 } },
            margin: { t: 50, r: 20, l: 40, b: 40 },
            xaxis: { gridcolor: gridColor, zerolinecolor: gridColor },
            yaxis: { gridcolor: gridColor, zerolinecolor: gridColor }
        };

        // ── Line Chart ────────────────────────────────────────────
        const realFrames      = globalResults.video_total_frames || globalResults.total_frames;
        const processedFrames = globalResults.processed_frames   || globalResults.total_frames;
        const lineTrace1 = {
            x: globalResults.graph_data.frames,
            y: globalResults.graph_data.traffic,
            type: 'scatter', mode: 'lines',
            line: { color: '#3b82f6', width: 1.5, shape: 'linear' },
            fill: 'tozeroy', fillcolor: 'rgba(59, 130, 246, 0.08)',
            name: 'Actual Traffic'
        };
        const lineTrace2 = {
            x: globalResults.graph_data.pred_frames,
            y: globalResults.graph_data.pred_traffic,
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: '#f97316', width: 2, shape: 'linear', dash: 'dash' },
            marker: { color: '#f97316', size: 5, symbol: 'circle' },
            name: `Prediction (${globalResults.pred_steps || ''} steps)`
        };
        Plotly.newPlot('line-chart', [lineTrace1, lineTrace2], {
            ...layoutTemplate,
            title: `Traffic Flow — ${processedFrames.toLocaleString()} of ${realFrames.toLocaleString()} frames analysed + ${globalResults.pred_steps || 200} predicted`,
            legend: { orientation: 'h', y: -0.2 }
        }, {responsive: true, displayModeBar: false});

        // ── Bar Chart ─────────────────────────────────────────────
        try {
            const dist = globalResults.graph_data.distribution || {};
            console.log('[BAR] raw distribution from API:', JSON.stringify(dist));

            // Defensive key lookup: handles both lowercase and Title-case keys
            const getCount = (lc, tc) => {
                const v = dist[lc] !== undefined ? dist[lc] : (dist[tc] !== undefined ? dist[tc] : 0);
                return Number(v) || 0;
            };

            const vehicleLabels = ['Cars', 'Motorcycles', 'Buses', 'Trucks'];
            const vehicleCounts = [
                getCount('cars',        'Cars'),
                getCount('motorcycles', 'Motorcycles'),
                getCount('buses',       'Buses'),
                getCount('trucks',      'Trucks')
            ];
            console.log('[BAR] vehicleCounts:', vehicleCounts);

            // Purge any previous chart to clear cached axis state
            Plotly.purge('bar-chart');

            const barTrace = {
                x: vehicleLabels,
                y: vehicleCounts,
                type: 'bar',
                text: vehicleCounts.map(v => v.toLocaleString()),
                textposition: 'auto',   // 'outside' causes silent crash on zero-height bars
                marker: {
                    color: [primaryColor, '#a855f7', '#22c55e', '#f59e0b'],
                    opacity: 0.85,
                    line: { color: 'rgba(255,255,255,0.15)', width: 1 }
                },
                hovertemplate: '<b>%{x}</b><br>Count: %{y:,}<extra></extra>'
            };

            Plotly.newPlot('bar-chart', [barTrace], {
                paper_bgcolor: 'transparent',
                plot_bgcolor:  'transparent',
                font:   { color: fontColor, family: "'Outfit', sans-serif" },
                title:  'Vehicle Distribution',
                titlefont: { color: titleColor, size: 16 },
                margin: { t: 50, r: 20, l: 55, b: 50 },
                xaxis: {
                    type: 'category',
                    gridcolor: gridColor,
                    zerolinecolor: 'transparent',
                    tickfont: { size: 13, color: fontColor }
                },
                yaxis: {
                    gridcolor: gridColor,
                    zerolinecolor: gridColor,
                    rangemode: 'tozero'
                },
                bargap: 0.3
            }, { responsive: true, displayModeBar: false });

            // ── Cross-Filtering Logic ──
            const barChartEl = document.getElementById('bar-chart');
            barChartEl.removeAllListeners('plotly_click');
            barChartEl.removeAllListeners('plotly_doubleclick');

            barChartEl.on('plotly_click', function(data){
                const clickedClass = data.points[0].label || data.points[0].x; // e.g. 'Cars'
                
                let filteredY = [];
                let traceName = '';
                
                if (clickedClass === 'Cars') {
                    filteredY = globalResults.graph_data.cars_traffic;
                    traceName = 'Cars Traffic';
                } else if (clickedClass === 'Motorcycles') {
                    filteredY = globalResults.graph_data.motorcycles_traffic;
                    traceName = 'Motorcycles Traffic';
                } else if (clickedClass === 'Buses') {
                    filteredY = globalResults.graph_data.buses_traffic;
                    traceName = 'Buses Traffic';
                } else if (clickedClass === 'Trucks') {
                    filteredY = globalResults.graph_data.trucks_traffic;
                    traceName = 'Trucks Traffic';
                }
                
                if (filteredY && filteredY.length > 0) {
                    Plotly.update('line-chart', { y: [filteredY], name: [traceName] }, {}, [0]);
                }
            });
            
            barChartEl.on('plotly_doubleclick', function(){
                Plotly.update('line-chart', { y: [globalResults.graph_data.traffic], name: ['Actual Traffic'] }, {}, [0]);
            });

        } catch (barErr) {
            console.error('[BAR] Bar chart render failed:', barErr);
        }

        // ── Cross-Filtering Logic ──
        try {
            const barChartEl = document.getElementById('bar-chart');
            if (barChartEl) {
                barChartEl.removeAllListeners('plotly_click');
                barChartEl.removeAllListeners('plotly_doubleclick');

                barChartEl.on('plotly_click', function(data){
                    const clickedClass = data.points[0].label || data.points[0].x;
                    
                    let filteredY = [];
                    let traceName = '';
                    
                    if (clickedClass === 'Cars') {
                        filteredY = globalResults.graph_data.cars_traffic;
                        traceName = 'Cars Traffic';
                    } else if (clickedClass === 'Motorcycles') {
                        filteredY = globalResults.graph_data.motorcycles_traffic;
                        traceName = 'Motorcycles Traffic';
                    } else if (clickedClass === 'Buses') {
                        filteredY = globalResults.graph_data.buses_traffic;
                        traceName = 'Buses Traffic';
                    } else if (clickedClass === 'Trucks') {
                        filteredY = globalResults.graph_data.trucks_traffic;
                        traceName = 'Trucks Traffic';
                    }
                    
                    if (filteredY && filteredY.length > 0) {
                        Plotly.update('line-chart', { y: [filteredY], name: [traceName] }, {}, [0]);
                    }
                });
                
                barChartEl.on('plotly_doubleclick', function(){
                    Plotly.update('line-chart', { y: [globalResults.graph_data.traffic], name: ['Actual Traffic'] }, {}, [0]);
                });
            }
        } catch (filterErr) {
            console.error('[FILTER] Cross-filtering binding failed:', filterErr);
        }

        // ── Premium Traffic Load Panel ─────────────────────────────
        try {
            renderTrafficLoadPanel();
        } catch (err) {
            console.error('[TLP] Traffic Load Panel render failed:', err);
        }

        function renderTrafficLoadPanel() {
            const avgVeh = globalResults.avg_veh || 0;
            const maxVeh = globalResults.max_veh || 1;
            const level = (globalResults.traffic_level || 'LOW').toUpperCase();

            // Calculate load percentage (dynamic ceiling based on data)
            const ceiling = Math.max(40, maxVeh * 1.5);
            const loadPct = Math.min(100, Math.round((avgVeh / ceiling) * 100));

            // Ring animation
            const ring = document.getElementById('tlp-ring-progress');
            const circumference = 2 * Math.PI * 85; // r=85
            const offset = circumference - (loadPct / 100) * circumference;
            setTimeout(() => { ring.style.strokeDashoffset = offset; }, 100);

            // Percentage display with counting animation
            const pctEl = document.getElementById('tlp-pct');
            let currentPct = 0;
            const pctInterval = setInterval(() => {
                currentPct += Math.max(1, Math.floor(loadPct / 30));
                if (currentPct >= loadPct) { currentPct = loadPct; clearInterval(pctInterval); }
                pctEl.textContent = currentPct + '%';
            }, 40);

            // Color scheme per level
            const colorMap = {
                'LOW':      { c1: '#10b981', c2: '#00f0ff', glow: 'rgba(16,185,129,0.12)', badge: '#10b981' },
                'MEDIUM':   { c1: '#f0c808', c2: '#f59e0b', glow: 'rgba(245,158,11,0.12)', badge: '#f59e0b' },
                'HIGH':     { c1: '#f97316', c2: '#ef4444', glow: 'rgba(249,115,22,0.15)', badge: '#f97316' },
                'CRITICAL': { c1: '#ef4444', c2: '#ff003c', glow: 'rgba(239,68,68,0.18)', badge: '#ff003c' }
            };
            const colors = colorMap[level] || colorMap['LOW'];

            // Gradient stops
            document.getElementById('ringGradStop1').setAttribute('stop-color', colors.c1);
            document.getElementById('ringGradStop2').setAttribute('stop-color', colors.c2);

            // Badge
            const badge = document.getElementById('tlp-badge');
            badge.textContent = level;
            badge.style.color = colors.badge;
            badge.style.borderColor = colors.badge;
            badge.style.background = colors.glow;

            // Panel glow
            const panel = document.getElementById('traffic-load-panel');
            panel.style.setProperty('--tlp-glow', colors.glow);
            panel.style.boxShadow = `0 0 40px ${colors.glow}, 0 8px 32px rgba(0,0,0,0.37)`;

            // Metrics
            document.getElementById('tlp-avg').textContent = avgVeh.toFixed(1);
            document.getElementById('tlp-peak').textContent = maxVeh;

            // Avg speed from traffic data
            const trafficData = globalResults.graph_data.traffic || [];
            const avgTraffic = trafficData.length > 0 ? (trafficData.reduce((a,b) => a+b, 0) / trafficData.length) : 0;
            document.getElementById('tlp-speed').textContent = avgTraffic.toFixed(1) + ' v/f';

            // Risk score
            let riskScore = Math.round((avgVeh / 15) * 18);
            riskScore = Math.min(100, Math.max(0, riskScore));
            document.getElementById('tlp-risk').textContent = riskScore + '/100';

            // Trend indicator
            const trendEl = document.getElementById('tlp-trend');
            if (trafficData.length >= 10) {
                const firstHalf = trafficData.slice(0, Math.floor(trafficData.length / 2));
                const secondHalf = trafficData.slice(Math.floor(trafficData.length / 2));
                const avgFirst = firstHalf.reduce((a,b) => a+b, 0) / firstHalf.length;
                const avgSecond = secondHalf.reduce((a,b) => a+b, 0) / secondHalf.length;
                const diff = avgSecond - avgFirst;
                if (diff > 1) {
                    trendEl.textContent = '↑ Increasing';
                    trendEl.style.color = '#f97316'; trendEl.style.borderColor = 'rgba(249,115,22,0.3)';
                } else if (diff < -1) {
                    trendEl.textContent = '↓ Decreasing';
                    trendEl.style.color = '#10b981'; trendEl.style.borderColor = 'rgba(16,185,129,0.3)';
                } else {
                    trendEl.textContent = '→ Stable';
                    trendEl.style.color = '#00f0ff'; trendEl.style.borderColor = 'rgba(0,240,255,0.3)';
                }
            }

            // AI interpretation
            const aiEl = document.getElementById('tlp-ai-text');
            const interpretations = {
                'LOW': `Traffic remains light with avg ${avgVeh.toFixed(1)} vehicles/frame. Low congestion risk.`,
                'MEDIUM': `Moderate traffic — ${avgVeh.toFixed(1)} avg vehicles. Monitor for peak-hour escalation.`,
                'HIGH': `Heavy flow — ${avgVeh.toFixed(1)} avg, peak ${maxVeh}. Congestion risk elevated.`,
                'CRITICAL': `Critical congestion — ${avgVeh.toFixed(1)} avg, peak ${maxVeh}. Immediate attention needed.`
            };
            aiEl.textContent = interpretations[level] || interpretations['LOW'];
        }

        // ── Premium Canvas Heatmap ───────────────────────────────
        try {
            renderCanvasHeatmap();
        } catch (err) {
            console.error('[HEATMAP] Canvas heatmap render failed:', err);
        }

        function renderCanvasHeatmap() {
            const canvas = document.getElementById('heatmap-canvas');
            const wrapper = canvas.parentElement;
            const tooltip = document.getElementById('hm-tooltip');
            const ctx = canvas.getContext('2d');

            const vehicleTypes = ['Cars', 'Motorcycles', 'Buses', 'Trucks'];
            const dataKeys = ['cars_traffic', 'motorcycles_traffic', 'buses_traffic', 'trucks_traffic'];
            const frames = globalResults.graph_data.frames || [];

            // Build data rows and detect low-activity
            const rows = dataKeys.map(k => globalResults.graph_data[k] || []);
            const rowMaxes = rows.map(r => Math.max(...r, 0));
            const globalMax = Math.max(...rowMaxes, 1);
            const isLowActivity = rowMaxes.map(m => m <= 1);

            // Filter out rows that are ALL zero (collapse empty rows)
            const activeIndices = [];
            const collapsedTypes = [];
            for (let i = 0; i < rows.length; i++) {
                if (rowMaxes[i] > 0) {
                    activeIndices.push(i);
                } else {
                    collapsedTypes.push(vehicleTypes[i]);
                }
            }
            // Always show at least the active rows (minimum 1)
            const displayIndices = activeIndices.length > 0 ? activeIndices : [0];

            // Canvas sizing
            const labelWidth = 90;
            const cellW = Math.max(2, Math.min(8, Math.floor((wrapper.clientWidth - labelWidth - 20) / frames.length)));
            const rowH = Math.max(40, Math.min(70, Math.floor(280 / displayIndices.length)));
            const canvasW = labelWidth + frames.length * cellW + 20;
            const canvasH = displayIndices.length * rowH + 30; // +30 for bottom axis
            canvas.width = canvasW * window.devicePixelRatio;
            canvas.height = canvasH * window.devicePixelRatio;
            canvas.style.width = canvasW + 'px';
            canvas.style.height = canvasH + 'px';
            ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

            // Traffic color gradient: Deep Blue → Cyan → Yellow → Orange → Red
            function getDensityColor(value, max) {
                const t = max > 0 ? value / max : 0; // 0..1
                if (t < 0.25) {
                    // Deep Blue → Cyan
                    const s = t / 0.25;
                    return lerpColor([10, 36, 99], [0, 180, 216], s);
                } else if (t < 0.5) {
                    // Cyan → Yellow
                    const s = (t - 0.25) / 0.25;
                    return lerpColor([0, 180, 216], [240, 200, 8], s);
                } else if (t < 0.75) {
                    // Yellow → Orange
                    const s = (t - 0.5) / 0.25;
                    return lerpColor([240, 200, 8], [249, 115, 22], s);
                } else {
                    // Orange → Red
                    const s = (t - 0.75) / 0.25;
                    return lerpColor([249, 115, 22], [230, 57, 70], s);
                }
            }

            function lerpColor(a, b, t) {
                return `rgb(${Math.round(a[0]+(b[0]-a[0])*t)},${Math.round(a[1]+(b[1]-a[1])*t)},${Math.round(a[2]+(b[2]-a[2])*t)})`;
            }

            function getDensityLevel(value, max) {
                const t = max > 0 ? value / max : 0;
                if (t < 0.25) return { text: 'Low', color: '#0a2463' };
                if (t < 0.5) return { text: 'Medium', color: '#00b4d8' };
                if (t < 0.75) return { text: 'High', color: '#f0c808' };
                return { text: 'Critical', color: '#e63946' };
            }

            // Draw heatmap
            ctx.clearRect(0, 0, canvasW, canvasH);

            displayIndices.forEach((ri, di) => {
                const row = rows[ri];
                const y = di * rowH;

                // Row label
                ctx.fillStyle = isLowActivity[ri] ? '#4a5568' : '#8b9bb4';
                ctx.font = '11px "Outfit", sans-serif';
                ctx.textAlign = 'right';
                ctx.textBaseline = 'middle';
                ctx.fillText(vehicleTypes[ri], labelWidth - 10, y + rowH / 2);

                // Cells
                for (let fi = 0; fi < frames.length; fi++) {
                    const val = row[fi] || 0;
                    const x = labelWidth + fi * cellW;

                    if (isLowActivity[ri] && val <= 0) {
                        ctx.fillStyle = 'rgba(10,15,30,0.6)';
                    } else {
                        ctx.fillStyle = getDensityColor(val, globalMax);
                    }
                    ctx.fillRect(x, y + 1, cellW - 0.5, rowH - 2);
                }

                // "Low Activity" overlay for low-activity rows
                if (isLowActivity[ri]) {
                    ctx.fillStyle = 'rgba(10,15,30,0.5)';
                    ctx.fillRect(labelWidth, y, frames.length * cellW, rowH);
                    ctx.fillStyle = '#4a5568';
                    ctx.font = '10px "JetBrains Mono", monospace';
                    ctx.textAlign = 'center';
                    ctx.fillText('LOW ACTIVITY', labelWidth + (frames.length * cellW) / 2, y + rowH / 2);
                }
            });

            // Bottom axis (frame number ticks)
            const tickEvery = Math.max(1, Math.floor(frames.length / 8));
            ctx.fillStyle = '#4a5568';
            ctx.font = '9px "JetBrains Mono", monospace';
            ctx.textAlign = 'center';
            for (let fi = 0; fi < frames.length; fi += tickEvery) {
                const x = labelWidth + fi * cellW + cellW / 2;
                ctx.fillText(frames[fi], x, displayIndices.length * rowH + 18);
            }

            // Summary stats
            let peakVal = 0, peakFrame = 0, peakTypeIdx = 0;
            rows.forEach((row, ri) => {
                row.forEach((val, fi) => {
                    if (val > peakVal) { peakVal = val; peakFrame = frames[fi]; peakTypeIdx = ri; }
                });
            });
            document.getElementById('hm-peak').textContent = 'Frame ' + peakFrame;
            document.getElementById('hm-type').textContent = vehicleTypes[peakTypeIdx];

            // Congestion zones: count frame ranges where total > 60% of globalMax
            const threshold = globalMax * 0.6;
            let zones = 0, inZone = false;
            for (let fi = 0; fi < frames.length; fi++) {
                const total = rows.reduce((s, r) => s + (r[fi] || 0), 0);
                if (total >= threshold && !inZone) { zones++; inZone = true; }
                else if (total < threshold) { inZone = false; }
            }
            document.getElementById('hm-zones').textContent = zones;

            // Hover tooltip
            canvas.addEventListener('mousemove', function(e) {
                const rect = canvas.getBoundingClientRect();
                const mx = e.clientX - rect.left;
                const my = e.clientY - rect.top;

                const fi = Math.floor((mx - labelWidth) / cellW);
                const di = Math.floor(my / rowH);

                if (fi >= 0 && fi < frames.length && di >= 0 && di < displayIndices.length) {
                    const ri = displayIndices[di];
                    const val = rows[ri][fi] || 0;
                    const level = getDensityLevel(val, globalMax);

                    tooltip.innerHTML = `
                        <div class="tt-label">Frame</div><div class="tt-val">${frames[fi]}</div>
                        <div class="tt-label">Vehicle Type</div><div class="tt-val">${vehicleTypes[ri]}</div>
                        <div class="tt-label">Count</div><div class="tt-val">${val}</div>
                        <div class="tt-label">Density</div><div class="tt-level" style="background:${level.color};color:#fff;">${level.text}</div>
                    `;
                    tooltip.style.display = 'block';
                    tooltip.style.left = Math.min(mx + 12, wrapper.clientWidth - 180) + 'px';
                    tooltip.style.top = (my + 12) + 'px';
                } else {
                    tooltip.style.display = 'none';
                }
            });
            canvas.addEventListener('mouseleave', () => { tooltip.style.display = 'none'; });
        }

        // --- Init Feature 1: Time Travel Slider ---
        initTimeTravelSlider();

        // --- Init Feature 2 & 3: Scenario Simulator & Risk Score ---
        initScenarioAndRisk();

        // --- Init Feature 4: RAG Copilot Chat ---
        initRAGChat();
    }

    // --- FEATURE 4: RAG Copilot Chat Logic ---
    function initRAGChat() {
        const toggleBtn = document.getElementById('chat-toggle-btn');
        const panel = document.getElementById('chat-panel');
        const closeBtn = document.getElementById('chat-close-btn');
        const sendBtn = document.getElementById('chat-send-btn');
        const inputField = document.getElementById('chat-input');
        const messagesDiv = document.getElementById('chat-messages');

        if (!toggleBtn || !panel) return;

        // Unhide the floating button only after results are ready
        toggleBtn.classList.remove('hidden');

        toggleBtn.addEventListener('click', () => {
            panel.classList.toggle('hidden');
        });

        closeBtn.addEventListener('click', () => {
            panel.classList.add('hidden');
        });

        async function sendMessage() {
            const text = inputField.value.trim();
            if (!text) return;

            // Display User Message
            const userMsg = document.createElement('div');
            userMsg.className = 'chat-msg user-msg';
            userMsg.innerText = text;
            messagesDiv.appendChild(userMsg);
            
            inputField.value = '';
            messagesDiv.scrollTop = messagesDiv.scrollHeight;

            // Loading state
            const loadingMsg = document.createElement('div');
            loadingMsg.className = 'chat-msg ai-msg';
            loadingMsg.innerHTML = '<span class="typewriter-text">Thinking...</span>';
            messagesDiv.appendChild(loadingMsg);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                const data = await response.json();
                
                loadingMsg.innerText = data.reply || data.error || "Connection error.";
            } catch (err) {
                loadingMsg.innerText = "Sorry, I couldn't connect to the Copilot Engine.";
            }
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        sendBtn.addEventListener('click', sendMessage);
        inputField.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }

    // --- FEATURE 2 & 3: Scenario Simulator & Risk Score Logic ---
    function initScenarioAndRisk() {
        if (!globalResults) return;
        
        const scenarioSelect = document.getElementById('scenario-select');
        const scenarioImpact = document.getElementById('scenario-impact');
        const riskScoreVal = document.getElementById('risk-score-val');
        const riskScoreLabel = document.getElementById('risk-score-label');
        if (!scenarioSelect || !riskScoreVal) return;

        // Base data for predictions
        const basePredTraffic = [...globalResults.graph_data.pred_traffic];
        const baseAvgVeh = globalResults.avg_veh;
        const maxCapacityThreshold = 80; // Example dynamic threshold

        function updateSimulation() {
            const multiplier = parseFloat(scenarioSelect.value);
            const increasePct = Math.round((multiplier - 1.0) * 100);
            
            // 1. Update Scenario Text
            scenarioImpact.innerText = `Impact: +${increasePct}% Expected Congestion`;
            
            // 2. Update Plotly Line Chart Prediction Curve
            if (multiplier !== 1.0) {
                const simulatedPred = basePredTraffic.map(v => Math.round(v * multiplier));
                // Update just the second trace (Prediction trace)
                Plotly.restyle('line-chart', 'y', [simulatedPred], [1]);
            } else {
                Plotly.restyle('line-chart', 'y', [basePredTraffic], [1]);
            }

            // 3. Compute Risk Score
            // Base score mapped dynamically to 20-30 based on typical 10-15 average vehicles.
            let simulatedAvg = baseAvgVeh * multiplier;
            
            // Formula: Scale simulated average non-linearly to quickly escalate risk during scenarios
            let score = Math.round((simulatedAvg / 15) * 18 * (multiplier * 0.8));
            score = Math.min(100, Math.max(0, score)); // Clamp 0-100

            // 4. Update Risk Score UI
            riskScoreVal.innerText = score.toString();
            
            // Remove old styling
            riskScoreLabel.style.background = '';
            riskScoreLabel.style.borderColor = '';
            riskScoreVal.style.color = '';

            if (score < 40) {
                riskScoreLabel.innerText = 'LOW RISK';
                riskScoreLabel.style.background = 'rgba(16, 185, 129, 0.2)';
                riskScoreLabel.style.borderColor = 'rgba(16, 185, 129, 0.8)';
                riskScoreVal.style.color = 'var(--success)';
                riskScoreLabel.style.color = 'var(--success)';
            } else if (score < 70) {
                riskScoreLabel.innerText = 'MEDIUM RISK';
                riskScoreLabel.style.background = 'rgba(245, 158, 11, 0.2)';
                riskScoreLabel.style.borderColor = 'rgba(245, 158, 11, 0.8)';
                riskScoreVal.style.color = 'var(--warning)';
                riskScoreLabel.style.color = 'var(--warning)';
            } else if (score < 85) {
                riskScoreLabel.innerText = 'HIGH RISK';
                riskScoreLabel.style.background = 'rgba(239, 68, 68, 0.2)';
                riskScoreLabel.style.borderColor = 'rgba(239, 68, 68, 0.8)';
                riskScoreVal.style.color = 'var(--danger)';
                riskScoreLabel.style.color = 'var(--danger)';
            } else {
                riskScoreLabel.innerText = 'CRITICAL';
                riskScoreLabel.style.background = 'rgba(255, 0, 0, 0.3)';
                riskScoreLabel.style.borderColor = 'rgba(255, 0, 0, 1)';
                riskScoreVal.style.color = '#ff0000';
                riskScoreLabel.style.color = '#ff0000';
            }
        }

        // Run initially to set the baseline risk score
        updateSimulation();

        // Listen for changes
        scenarioSelect.addEventListener('change', updateSimulation);
    }

    // --- FEATURE 1: Time Travel Slider Logic ---
    function initTimeTravelSlider() {
        if (!globalResults) return;
        const timeSlider = document.getElementById('time-slider');
        const timeDisplay = document.getElementById('time-display');
        if (!timeSlider || !timeDisplay) return;

        const actualFrames = globalResults.graph_data.frames;
        const predFrames = globalResults.graph_data.pred_frames;
        
        // Combine frames, excluding the duplicate anchor frame from predictions
        const totalTimeline = [...actualFrames, ...predFrames.slice(1)];
        timeSlider.max = totalTimeline.length - 1;
        timeSlider.value = totalTimeline.length - 1; // Default to end
        timeDisplay.innerText = `Frame: ${totalTimeline[timeSlider.value]}`;

        timeSlider.addEventListener('input', (e) => {
            const idx = parseInt(e.target.value);
            const frameNum = totalTimeline[idx];
            
            let status = (idx < actualFrames.length) ? 'Historical' : 'Predicted';
            timeDisplay.innerText = `${status} Frame: ${frameNum}`;
            timeDisplay.style.color = (idx < actualFrames.length) ? 'var(--primary)' : 'var(--warning)';

            // 1. Draw vertical line on the Plotly Line Chart
            Plotly.relayout('line-chart', {
                shapes: [{
                    type: 'line',
                    x0: frameNum, y0: 0,
                    x1: frameNum, y1: 1,
                    yref: 'paper',
                    line: { color: 'var(--primary)', width: 2, dash: 'dot' }
                }]
            });

            // 2. Sync Video (if within historical bounds)
            if (idx < actualFrames.length) {
                // Approximate time in seconds (assuming ~10fps or similar, we can map linearly if exact fps is unknown)
                // We know outputVideo duration.
                if (outputVideo && outputVideo.duration) {
                    const progress = idx / (actualFrames.length - 1);
                    outputVideo.currentTime = progress * outputVideo.duration;
                }
            }
        });
    }

    // --- Report Generation ---
    if (btnGenerateReport) {
        btnGenerateReport.addEventListener('click', async () => {
            btnGenerateReport.disabled = true;
            btnGenerateReport.innerText = "GENERATING...";
            reportStatus.classList.remove('hidden');
            reportStatus.style.color = "var(--primary)";
            reportStatus.innerText = "> Building PDF report, please wait...";

            try {
                const response = await fetch('/api/report', { method: 'POST' });
                if (response.ok) {
                    // Trigger download
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'traffic_report.pdf';
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    window.URL.revokeObjectURL(url);
                    reportStatus.style.color = "var(--success)";
                    reportStatus.innerText = "> PDF report downloaded successfully!";
                    btnGenerateReport.innerText = "DOWNLOAD REPORT";
                } else {
                    const data = await response.json();
                    reportStatus.style.color = "var(--danger)";
                    reportStatus.innerText = `> ERROR: ${data.error}`;
                    btnGenerateReport.innerText = "GENERATE REPORT";
                }
            } catch (error) {
                reportStatus.style.color = "var(--danger)";
                reportStatus.innerText = "> ERROR: Connection failed.";
                btnGenerateReport.innerText = "GENERATE REPORT";
            } finally {
                btnGenerateReport.disabled = false;
            }
        });
    }
    
    if (btnSendReport) {
        btnSendReport.addEventListener('click', async () => {
            const emailInput = document.getElementById('report-email').value;
            if (!emailInput) {
                alert("Please enter a valid Gmail address first!");
                return;
            }
            
            btnSendReport.disabled = true;
            btnSendReport.innerText = "SENDING...";
            reportStatus.classList.remove('hidden');
            reportStatus.style.color = "var(--primary)";
            reportStatus.innerText = "> DISPATCHING EMAIL...";

            try {
                const response = await fetch('/api/send_report', { 
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: emailInput })
                });
                const data = await response.json();

                if (response.ok) {
                    reportStatus.style.color = "var(--success)";
                    reportStatus.innerText = `> SUCCESS: ${data.message}`;
                    btnSendReport.innerText = "SENT SUCCESSFULLY";
                } else {
                    reportStatus.style.color = "var(--danger)";
                    reportStatus.innerText = `> ERROR: ${data.error}`;
                    btnSendReport.disabled = false;
                    btnSendReport.innerText = "SEND TO EMAIL";
                }
            } catch (error) {
                reportStatus.style.color = "var(--danger)";
                reportStatus.innerText = `> ERROR: Connection failed.`;
                btnSendReport.disabled = false;
                btnSendReport.innerText = "SEND TO EMAIL";
            }
        });
    }
});
