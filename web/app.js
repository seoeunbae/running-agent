// API endpoint configuration
const API_URL = '/api/chat';

// Select DOM elements
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatMessages = document.getElementById('chat-messages');
const sendButton = document.getElementById('send-button');

// Pipeline DOM elements
const pipelineIdle = document.getElementById('pipeline-idle');
const pipelineActive = document.getElementById('pipeline-active');

// Pipeline Step Elements
const stepWeather = document.getElementById('step-weather');
const stepRoute = document.getElementById('step-route');
const stepFacilities = document.getElementById('step-facilities');
const stepFallback = document.getElementById('step-fallback');
const stepRunning = document.getElementById('step-running');

// Pipeline Data Elements
const dataWeather = document.getElementById('data-weather');
const dataRoute = document.getElementById('data-route');
const dataFacilities = document.getElementById('data-facilities');
const dataFallback = document.getElementById('data-fallback');
const dataRunning = document.getElementById('data-running');

// Select preset query
function selectPreset(promptText) {
    chatInput.value = promptText;
    chatInput.focus();
}

// Format markdown-like text to HTML helper
function parseMarkdown(text) {
    if (!text) return '';

    let html = text;

    // Replace headers
    html = html.replace(/\n\s*\*\*(.*?)\*\*/g, '<br><h3>$1</h3>');
    html = html.replace(/\s*\*\*(.*?)\*\*/g, ' <strong>$1</strong>');

    // Replace bullet lists
    html = html.replace(/\n-\s*(.*?)/g, '<br>• $1');
    html = html.replace(/➔/g, '<i class="fa-solid fa-arrow-right"></i>');

    return html;
}

// Add a message to the chat window
function addMessage(sender, text, isHtml = false) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender);

    const avatar = document.createElement('div');
    avatar.classList.add('message-avatar');
    avatar.innerHTML = sender === 'user' ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';

    const bubble = document.createElement('div');
    bubble.classList.add('message-bubble');

    if (isHtml) {
        bubble.innerHTML = text;
    } else {
        bubble.textContent = text;
    }

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);
    chatMessages.appendChild(messageDiv);

    // Scroll chat to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return messageDiv;
}

// Show a temporary typing indicator message
function showTypingIndicator() {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', 'assistant', 'typing-message');

    const avatar = document.createElement('div');
    avatar.classList.add('message-avatar');
    avatar.innerHTML = '<i class="fa-solid fa-robot"></i>';

    const bubble = document.createElement('div');
    bubble.classList.add('message-bubble');
    bubble.innerHTML = `
        <div class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return messageDiv;
}

// Reset pipeline tracker elements
function resetPipelineTracker() {
    pipelineIdle.style.display = 'none';
    pipelineActive.style.display = 'flex';

    // Reset classes
    const steps = [stepWeather, stepRoute, stepFacilities, stepFallback, stepRunning];
    steps.forEach(step => {
        step.className = 'pipeline-step';
        const badge = step.querySelector('.step-badge');
        badge.textContent = '대기 중';
        badge.className = 'step-badge pending';
    });

    // Hide data panels
    const dataContainers = [dataWeather, dataRoute, dataFacilities, dataFallback, dataRunning];
    dataContainers.forEach(container => {
        container.style.display = 'none';
        container.innerHTML = '';
    });
}

// Animate the pipeline orchestrator step-by-step using captured ADK events
async function playOrchestrationAnimation(events, image) {
    resetPipelineTracker();

    // Helper to pause execution to simulate real-time API call delay
    const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

    // Step 1: Weather check (get_weather_forecast)
    const weatherCall = events.find(e => e.type === 'ToolCallEvent' && e.tool_name === 'get_weather_forecast');
    const weatherResp = events.find(e => e.type === 'ToolResponseEvent' && e.tool_name === 'get_weather_forecast');

    if (weatherCall && weatherResp) {
        stepWeather.classList.add('active');
        stepWeather.querySelector('.step-badge').textContent = '진행 중';
        stepWeather.querySelector('.step-badge').className = 'step-badge running';
        await delay(1200);

        stepWeather.classList.remove('active');
        stepWeather.classList.add('completed');

        const prob = weatherResp.response.rain_probability;
        const isRain = prob >= 0.50;

        const weatherBadge = stepWeather.querySelector('.step-badge');
        if (isRain) {
            weatherBadge.textContent = '일정 연기';
            weatherBadge.className = 'step-badge alert';
            stepWeather.classList.add('alert-state');

            dataWeather.innerHTML = `
                <div class="data-param"><span class="data-label">위치:</span> <span class="data-val">${weatherResp.response.location}</span></div>
                <div class="data-param"><span class="data-label">기상 상태:</span> <span class="data-val alert"><i class="fa-solid fa-cloud-showers-heavy"></i> ${weatherResp.response.forecast}</span></div>
                <div class="data-param"><span class="data-label">조치:</span> <span class="data-val alert">강수 확률 50% 이상으로 일정을 다음 주로 자동 연기!</span></div>
            `;
        } else {
            weatherBadge.textContent = '맑음 확정';
            weatherBadge.className = 'step-badge done';

            dataWeather.innerHTML = `
                <div class="data-param"><span class="data-label">위치:</span> <span class="data-val">${weatherResp.response.location}</span></div>
                <div class="data-param"><span class="data-label">기상 상태:</span> <span class="data-val green"><i class="fa-solid fa-sun"></i> ${weatherResp.response.forecast}</span></div>
                <div class="data-param"><span class="data-label">조치:</span> <span class="data-val green">일정 정상 진행 확정!</span></div>
            `;
        }
        dataWeather.style.display = 'block';
        await delay(1000);
    }

    // Step 2: Route retrieval (get_route_elevation)
    const routeCall = events.find(e => e.type === 'ToolCallEvent' && e.tool_name === 'get_route_elevation');
    const routeResp = events.find(e => e.type === 'ToolResponseEvent' && e.tool_name === 'get_route_elevation');

    if (routeCall && routeResp) {
        stepRoute.classList.add('active');
        stepRoute.querySelector('.step-badge').textContent = '분석 중';
        stepRoute.querySelector('.step-badge').className = 'step-badge running';
        await delay(1200);

        stepRoute.classList.remove('active');
        stepRoute.classList.add('completed');
        stepRoute.querySelector('.step-badge').textContent = '완료';
        stepRoute.querySelector('.step-badge').className = 'step-badge done';

        dataRoute.innerHTML = `
            <div class="data-param"><span class="data-label">코스명:</span> <span class="data-val green">${routeResp.response.route_name}</span></div>
            <div class="data-param"><span class="data-label">구간:</span> <span class="data-val">${routeResp.response.start} ➔ ${routeResp.response.destination}</span></div>
            <div class="data-param"><span class="data-label">스펙:</span> <span class="data-val">거리 ${routeResp.response.distance} / 고도상승 ${routeResp.response.elevation_gain} (평탄)</span></div>
        `;
        dataRoute.style.display = 'block';
        await delay(1000);
    }

    // Step 3: Search facilities (search_nearby_facilities)
    // There can be multiple calls to facilities (primary attempt and fallback check).
    const facilityCalls = events.filter(e => e.type === 'ToolCallEvent' && e.tool_name === 'search_nearby_facilities');
    const facilityResps = events.filter(e => e.type === 'ToolResponseEvent' && e.tool_name === 'search_nearby_facilities');

    const primaryResp = facilityResps.find(r => r.response.status === 'NO_RESULTS_FOUND' || r.response.facilities.length === 0);
    const fallbackResp = facilityResps.find(r => r.response.status === 'SUCCESS');

    if (facilityCalls.length > 0) {
        stepFacilities.classList.add('active');
        stepFacilities.querySelector('.step-badge').textContent = '조회 중';
        stepFacilities.querySelector('.step-badge').className = 'step-badge running';
        await delay(1400);

        stepFacilities.classList.remove('active');
        stepFacilities.classList.add('completed');

        if (primaryResp) {
            // No campsites found at destination
            stepFacilities.querySelector('.step-badge').textContent = '결과 없음';
            stepFacilities.querySelector('.step-badge').className = 'step-badge alert';
            stepFacilities.classList.add('fallback-triggered'); // Special color class

            dataFacilities.innerHTML = `
                <div class="data-param"><span class="data-label">검색 위치:</span> <span class="data-val alert">자라섬 (도착점)</span></div>
                <div class="data-param"><span class="data-label">상태:</span> <span class="data-val alert"><i class="fa-solid fa-triangle-exclamation"></i> 예약 가능한 캠핑장 없음</span></div>
                <div class="data-param"><span class="data-label">알림:</span> <span class="data-val alert">가치사슬 중단 복구용 폴백 로직 자동 트리거!</span></div>
            `;
            dataFacilities.style.display = 'block';
            await delay(1200);

            // Step 4: Fallback execution
            stepFallback.classList.add('active');
            stepFallback.classList.add('fallback-triggered');
            stepFallback.querySelector('.step-badge').textContent = '폴백 가동';
            stepFallback.querySelector('.step-badge').className = 'step-badge alert';
            await delay(1400);

            stepFallback.classList.remove('active');
            stepFallback.classList.add('completed');
            stepFallback.querySelector('.step-badge').textContent = '폴백 해결';
            stepFallback.querySelector('.step-badge').className = 'step-badge done';

            if (fallbackResp) {
                const facList = fallbackResp.response.facilities.map(f => `<li>${f.name} (${f.distance})</li>`).join('');
                dataFallback.innerHTML = `
                    <div class="data-param"><span class="data-label">폴백 거점:</span> <span class="data-val green">가평역 (출발지)</span></div>
                    <div class="data-param"><span class="data-label">대체 시설:</span> <span class="data-val green">가용 캠핑장 2개소 탐색 성공</span></div>
                    <ul style="margin-left: 14px; margin-top: 5px; list-style-type: circle; color: var(--text-secondary); font-size: 11px;">
                        ${facList}
                    </ul>
                    <div class="data-param" style="margin-top:6px;"><span class="data-label">조율 계획:</span> <span class="data-val green">가평역 출발 역방향 가상 코스 수립 제안</span></div>
                `;
            }
            dataFallback.style.display = 'block';

        } else if (fallbackResp) {
            // Campsites found on first try
            stepFacilities.querySelector('.step-badge').textContent = '완료';
            stepFacilities.querySelector('.step-badge').className = 'step-badge done';

            const facList = fallbackResp.response.facilities.map(f => `<li>${f.name} (${f.distance})</li>`).join('');
            dataFacilities.innerHTML = `
                <div class="data-param"><span class="data-label">검색 위치:</span> <span class="data-val green">${fallbackResp.response.location}</span></div>
                <div class="data-param"><span class="data-label">시설 목록:</span></div>
                <ul style="margin-left: 14px; margin-top: 3px; list-style-type: circle; color: var(--text-secondary); font-size: 11px;">
                    ${facList}
                </ul>
            `;
            dataFacilities.style.display = 'block';
            await delay(1000);

            // Skip fallback step
            stepFallback.classList.add('skipped');
            stepFallback.querySelector('.step-badge').textContent = '생략';
            stepFallback.querySelector('.step-badge').className = 'step-badge pending';
        }
    }

    // Step 5: Running course (search_running_course)
    const runningCall = events.find(e => e.type === 'ToolCallEvent' && e.tool_name === 'search_running_course');
    const runningResp = events.find(e => e.type === 'ToolResponseEvent' && e.tool_name === 'search_running_course');

    if (runningCall) {
        stepRunning.classList.add('active');
        stepRunning.querySelector('.step-badge').textContent = '탐색 중';
        stepRunning.querySelector('.step-badge').className = 'step-badge running';
        await delay(1400);

        stepRunning.classList.remove('active');
        stepRunning.classList.add('completed');
        stepRunning.querySelector('.step-badge').textContent = '완료';
        stepRunning.querySelector('.step-badge').className = 'step-badge done';

        const hasImage = image && image.data;
        dataRunning.innerHTML = `
            <div class="data-param"><span class="data-label">위치:</span> <span class="data-val green">${runningCall.args.location || '-'}</span></div>
            <div class="data-param"><span class="data-label">목표 거리:</span> <span class="data-val">${runningCall.args.distance_km || 5.0}km</span></div>
            <div class="data-param"><span class="data-label">지도 이미지:</span> <span class="data-val ${hasImage ? 'green' : 'alert'}"><i class="fa-solid fa-${hasImage ? 'map' : 'triangle-exclamation'}"></i> ${hasImage ? '생성 완료' : 'GOOGLE_MAPS_API_KEY 필요'}</span></div>
        `;
        dataRunning.style.display = 'block';
    } else {
        stepRunning.classList.add('skipped');
        stepRunning.querySelector('.step-badge').textContent = '생략';
        stepRunning.querySelector('.step-badge').className = 'step-badge pending';
    }
}

// Submit prompt to backend API
async function handleChatSubmit(event) {
    event.preventDefault();

    const messageText = chatInput.value.trim();
    if (!messageText) return;

    // Add user message bubble
    addMessage('user', messageText);
    chatInput.value = '';

    // Disable inputs during processing
    chatInput.disabled = true;
    sendButton.disabled = true;

    // Show typing animation
    const typingMessage = showTypingIndicator();

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: messageText }),
        });

        const data = await response.json();

        // Remove typing indicator
        if (typingMessage) {
            typingMessage.remove();
        }

        if (data.success) {
            // 1. Play orchestration animation based on backend events
            await playOrchestrationAnimation(data.events, data.image);
            console.log("pass data.success!")
            // 2. Add final assistant response bubble with markdown rendering
            let htmlResponse = parseMarkdown(data.text);

            if (data.image && data.image.data) {

                htmlResponse += `
                    <div style="margin-top:12px;">
                        <img src="data:${data.image.mime_type};base64,${data.image.data}"
                             alt="러닝 코스 지도"
                             style="width:100%;max-width:420px;border-radius:10px;border:1px solid rgba(255,255,255,0.15);" />
                        <p style="font-size:11px;color:var(--text-secondary);margin-top:4px;"><i class="fa-solid fa-map-pin"></i> ${data.image.filename}</p>
                    </div>`;
            }
            addMessage('assistant', htmlResponse, true);
        } else {
            addMessage('assistant', `에러가 발생했습니다: ${data.error || '알 수 없는 서버 오류'}`);
        }

    } catch (error) {
        if (typingMessage) {
            typingMessage.remove();
        }
        addMessage('assistant', `서버와 통신하는 중 장애가 발생했습니다: ${error.message}`);
        console.error(error);
    } finally {
        chatInput.disabled = false;
        sendButton.disabled = false;
        chatInput.focus();
    }
}
