const API_BASE = window.location.origin + '/api/v1';

const params = new URLSearchParams(window.location.search);
const SHOP_ID = params.get('shop_id');

const cameraInput = document.getElementById('camera-input');
const galleryInput = document.getElementById('gallery-input');
const fileList = document.getElementById('file-list');
const filesList = document.getElementById('files');
const sendBtn = document.getElementById('send-btn');
const uploadSection = document.getElementById('upload-section');
const progressSection = document.getElementById('progress-section');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');
const statusSection = document.getElementById('status-section');
const statusMessage = document.getElementById('status-message');
const doneSection = document.getElementById('done-section');
const errorSection = document.getElementById('error-section');
const errorMessage = document.getElementById('error-message');
const uploadMoreBtn = document.getElementById('upload-more-btn');
const retryBtn = document.getElementById('retry-btn');
const shopInfo = document.getElementById('shop-info');
const shopName = document.getElementById('shop-name');

let selectedFiles = [];

function init() {
    if (!SHOP_ID) {
        showError('No shop ID. Please scan the QR code or add ?shop_id=xxx to the URL.');
        return;
    }
    loadShopInfo();
    setupEventListeners();
}

async function loadShopInfo() {
    try {
        const res = await fetch(`${API_BASE}/shop/${SHOP_ID}`);
        if (res.ok) {
            const shop = await res.json();
            shopName.textContent = shop.shop_name;
            shopInfo.classList.remove('hidden');
        }
    } catch (e) {}
}

function setupEventListeners() {
    cameraInput.addEventListener('change', handleFileSelect);
    galleryInput.addEventListener('change', handleFileSelect);
    sendBtn.addEventListener('click', handleSend);
    uploadMoreBtn.addEventListener('click', resetUI);
    retryBtn.addEventListener('click', resetUI);
}

function handleFileSelect(e) {
    const newFiles = Array.from(e.target.files);
    selectedFiles = [...selectedFiles, ...newFiles];
    updateFileList();
    e.target.value = '';
}

function updateFileList() {
    if (selectedFiles.length === 0) {
        fileList.classList.add('hidden');
        sendBtn.classList.add('hidden');
        return;
    }

    fileList.classList.remove('hidden');
    sendBtn.classList.remove('hidden');
    sendBtn.disabled = false;

    filesList.innerHTML = '';
    selectedFiles.forEach((file, index) => {
        const li = document.createElement('li');
        li.innerHTML = `
            <span class="file-item-info">
                <span class="file-check">✓</span>
                ${file.name}
            </span>
            <button class="file-remove" data-index="${index}">&times;</button>
        `;
        filesList.appendChild(li);
    });

    document.querySelectorAll('.file-remove').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const index = parseInt(e.target.dataset.index);
            selectedFiles.splice(index, 1);
            updateFileList();
        });
    });
}

async function handleSend() {
    if (selectedFiles.length === 0) return;
    sendBtn.disabled = true;

    showProgress();
    const formData = new FormData();
    selectedFiles.forEach(file => {
        formData.append('files', file);
    });

    try {
        const response = await new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const pct = Math.round((e.loaded / e.total) * 100);
                    progressFill.style.width = pct + '%';
                    progressText.textContent = `Uploading... ${pct}%`;
                }
            });
            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve(JSON.parse(xhr.responseText));
                } else {
                    try {
                        const err = JSON.parse(xhr.responseText);
                        reject(new Error(err.detail?.error?.message || err.detail || 'Upload failed'));
                    } catch {
                        reject(new Error('Upload failed'));
                    }
                }
            };
            xhr.onerror = () => reject(new Error('Network error'));
            xhr.open('POST', `${API_BASE}/upload/${SHOP_ID}`);
            xhr.send(formData);
        });

        showStatus('Processing your documents...');
        pollJobStatus(response.job_id);

    } catch (err) {
        showError(err.message);
    }
}

async function pollJobStatus(jobId) {
    let attempt = 0;
    const maxAttempts = 120;

    const poll = async () => {
        if (attempt >= maxAttempts) {
            showError('Processing is taking longer than expected. Please wait.');
            return;
        }
        attempt++;

        try {
            const res = await fetch(`${API_BASE}/jobs/${jobId}`);
            if (!res.ok) throw new Error('Status check failed');
            const job = await res.json();

            const readyCount = job.documents.filter(d => d.status === 'READY').length;
            const failedCount = job.documents.filter(d => d.status === 'FAILED').length;
            const total = job.documents.length;

            if (job.status === 'READY' || job.status === 'PREVIEW') {
                showDone();
                return;
            }

            if (job.status === 'FAILED' && failedCount === total) {
                showError('Processing failed. Please try again.');
                return;
            }

            statusMessage.textContent = `Processing... (${readyCount + failedCount}/${total} done)`;
            setTimeout(poll, 2000);
        } catch (e) {
            setTimeout(poll, 3000);
        }
    };

    poll();
}

function showProgress() {
    uploadSection.classList.add('hidden');
    progressSection.classList.remove('hidden');
    progressFill.style.width = '0%';
}

function showStatus(msg) {
    progressSection.classList.add('hidden');
    statusSection.classList.remove('hidden');
    statusMessage.textContent = msg || 'Processing your document...';
}

function showDone() {
    statusSection.classList.add('hidden');
    doneSection.classList.remove('hidden');
}

function showError(msg) {
    uploadSection.classList.add('hidden');
    progressSection.classList.add('hidden');
    statusSection.classList.add('hidden');
    errorSection.classList.remove('hidden');
    errorMessage.textContent = msg;
}

function resetUI() {
    selectedFiles = [];
    uploadSection.classList.remove('hidden');
    progressSection.classList.add('hidden');
    statusSection.classList.add('hidden');
    doneSection.classList.add('hidden');
    errorSection.classList.add('hidden');
    fileList.classList.add('hidden');
    sendBtn.classList.add('hidden');
    sendBtn.disabled = false;
    filesList.innerHTML = '';
}

init();
