// TV Application JavaScript - Optimized for Large Screens

// Application State
const state = {
    currentScreen: 'home-screen',
    reports: [],
    currentAnalysis: null,
    isAnalyzing: false
};

// DOM Elements
const screens = {
    home: document.getElementById('home-screen'),
    upload: document.getElementById('upload-screen'),
    reports: document.getElementById('reports-screen'),
    learn: document.getElementById('learn-screen')
};

const uploadElements = {
    fileInput: document.getElementById('file-input'),
    dropArea: document.getElementById('drop-area'),
    analyzeBtn: document.getElementById('analyze-btn'),
    cancelBtn: document.getElementById('cancel-btn'),
    progressSection: document.getElementById('progress-section'),
    progressFill: document.getElementById('progress-fill'),
    progressText: document.getElementById('progress-text'),
    resultsSection: document.getElementById('results-section'),
    overallAssessment: document.getElementById('overall-assessment'),
    confidenceScore: document.getElementById('confidence-score'),
    analysisTime: document.getElementById('analysis-time'),
    behaviorsGrid: document.getElementById('behaviors-grid'),
    analysisTimestamp: document.getElementById('analysis-timestamp')
};

const reportsElements = {
    searchInput: document.getElementById('search-input'),
    reportsList: document.getElementById('reports-list')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', function () {
    initializeEventListeners();
    loadReports();
    setupDragAndDrop();
});

// Navigation Functions
function navigateTo(screenId) {
    // Hide all screens
    Object.values(screens).forEach(screen => {
        screen.classList.remove('active');
    });

    // Show target screen
    const targetScreen = screens[screenId.replace('-screen', '')];
    if (targetScreen) {
        targetScreen.classList.add('active');
        state.currentScreen = screenId;

        // Reset upload screen if navigating away
        if (screenId !== 'upload-screen') {
            resetUploadScreen();
        }

        // Load reports if navigating to reports screen
        if (screenId === 'reports-screen') {
            renderReports();
        }
    }
}

// Drag and Drop Functionality
function setupDragAndDrop() {
    const dropArea = uploadElements.dropArea;
    const fileInput = uploadElements.fileInput;

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    // Highlight drop area when dragging over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });

    // Handle dropped files
    dropArea.addEventListener('drop', handleDrop, false);

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight(e) {
        dropArea.classList.add('drag-over');
    }

    function unhighlight(e) {
        dropArea.classList.remove('drag-over');
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files && files.length > 0) {
            handleFiles(files);
        }
    }

    // Handle file input change
    fileInput.addEventListener('change', function (e) {
        if (this.files && this.files.length > 0) {
            handleFiles(this.files);
        }
    });
}

function handleFiles(files) {
    const file = files[0];

    if (!file.type.startsWith('video/')) {
        showNotification('Please select a video file', 'error');
        return;
    }

    // Enable analyze button
    uploadElements.analyzeBtn.disabled = false;
    uploadElements.cancelBtn.disabled = false;

    // Update drop area text
    const uploadContent = uploadElements.dropArea.querySelector('.upload-content');
    uploadContent.innerHTML = `
        <div class="upload-icon">✅</div>
        <h3>Video Selected</h3>
        <p>${file.name}</p>
        <p class="file-size">${formatFileSize(file.size)}</p>
        <button class="browse-btn" onclick="document.getElementById('file-input').click()">Change File</button>
    `;

    // Store file reference
    state.selectedFile = file;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Analysis Functions
function startAnalysis() {
    if (!state.selectedFile) {
        showNotification('Please select a video file first', 'error');
        return;
    }

    if (state.isAnalyzing) {
        showNotification('Analysis already in progress', 'warning');
        return;
    }

    state.isAnalyzing = true;
    state.currentAnalysis = {
        file: state.selectedFile,
        startTime: new Date(),
        progress: 0
    };

    // Hide upload section, show progress
    uploadElements.dropArea.style.display = 'none';
    uploadElements.analyzeBtn.style.display = 'none';
    uploadElements.cancelBtn.style.display = 'block';
    uploadElements.progressSection.style.display = 'block';
    uploadElements.resultsSection.style.display = 'none';

    // Start simulated analysis
    simulateAnalysis();
}

function simulateAnalysis() {
    const totalSteps = 100;
    let currentStep = 0;
    const stepDuration = 100; // 100ms per step

    const progressInterval = setInterval(() => {
        if (!state.isAnalyzing) {
            clearInterval(progressInterval);
            return;
        }

        currentStep++;
        const progress = (currentStep / totalSteps) * 100;

        // Update progress bar
        uploadElements.progressFill.style.width = `${progress}%`;

        // Update progress text
        const messages = [
            'Initializing analysis...',
            'Processing video frames...',
            'Extracting behavioral features...',
            'Analyzing movement patterns...',
            'Detecting repetitive behaviors...',
            'Processing hand movements...',
            'Analyzing body movements...',
            'Reviewing eye contact patterns...',
            'Generating comprehensive report...',
            'Finalizing analysis...'
        ];

        const messageIndex = Math.floor(progress / 10);
        uploadElements.progressText.textContent = messages[messageIndex] || 'Analysis complete';

        if (currentStep >= totalSteps) {
            clearInterval(progressInterval);
            completeAnalysis();
        }
    }, stepDuration);
}

function completeAnalysis() {
    state.isAnalyzing = false;
    const endTime = new Date();
    const duration = Math.floor((endTime - state.currentAnalysis.startTime) / 1000);

    // Generate random but realistic results
    const results = generateAnalysisResults(state.selectedFile);

    // Update results section
    uploadElements.overallAssessment.textContent = results.overallAssessment;
    uploadElements.confidenceScore.textContent = `${results.confidenceScore}%`;
    uploadElements.analysisTime.textContent = `${duration}s`;
    uploadElements.analysisTimestamp.textContent = endTime.toLocaleString();

    // Set colors based on assessment
    const assessmentElement = uploadElements.overallAssessment;
    assessmentElement.className = 'result-value';
    if (results.overallAssessment.includes('Low')) {
        assessmentElement.style.color = '#10b981'; // Green
    } else if (results.overallAssessment.includes('Moderate')) {
        assessmentElement.style.color = '#f59e0b'; // Orange
    } else {
        assessmentElement.style.color = '#ef4444'; // Red
    }

    // Render behavior details
    renderBehaviors(results.behaviors);

    // Show results section
    uploadElements.progressSection.style.display = 'none';
    uploadElements.resultsSection.style.display = 'flex';

    // Save report
    saveReport(results);
}

function generateAnalysisResults(file) {
    // Generate random but realistic results
    const behaviors = [
        {
            name: 'Hand Flapping',
            icon: '✋',
            detected: Math.random() > 0.7,
            confidence: Math.floor(Math.random() * 40) + 60,
            duration: Math.floor(Math.random() * 30) + 5
        },
        {
            name: 'Body Spinning',
            icon: '🔄',
            detected: Math.random() > 0.8,
            confidence: Math.floor(Math.random() * 30) + 70,
            duration: Math.floor(Math.random() * 20) + 3
        },
        {
            name: 'Head Banging',
            icon: '🤕',
            detected: Math.random() > 0.9,
            confidence: Math.floor(Math.random() * 20) + 80,
            duration: Math.floor(Math.random() * 10) + 1
        },
        {
            name: 'Repetitive Movements',
            icon: '🔄',
            detected: Math.random() > 0.6,
            confidence: Math.floor(Math.random() * 50) + 50,
            duration: Math.floor(Math.random() * 40) + 10
        }
    ];

    const detectedBehaviors = behaviors.filter(b => b.detected);
    const totalConfidence = detectedBehaviors.reduce((sum, b) => sum + b.confidence, 0);
    const avgConfidence = detectedBehaviors.length > 0 ? totalConfidence / detectedBehaviors.length : 30;

    let overallAssessment;
    let confidenceScore;

    if (avgConfidence < 40) {
        overallAssessment = 'Low Probability';
        confidenceScore = Math.floor(avgConfidence);
    } else if (avgConfidence < 70) {
        overallAssessment = 'Moderate Probability';
        confidenceScore = Math.floor(avgConfidence);
    } else {
        overallAssessment = 'High Probability';
        confidenceScore = Math.floor(avgConfidence);
    }

    return {
        fileName: file.name,
        fileSize: file.size,
        overallAssessment,
        confidenceScore,
        behaviors,
        detectedCount: detectedBehaviors.length,
        timestamp: new Date().toISOString()
    };
}

function renderBehaviors(behaviors) {
    uploadElements.behaviorsGrid.innerHTML = '';

    behaviors.forEach(behavior => {
        const card = document.createElement('div');
        card.className = 'behavior-card';

        const icon = document.createElement('div');
        icon.className = 'behavior-icon';
        icon.textContent = behavior.icon;

        const content = document.createElement('div');
        content.className = 'behavior-content';

        const title = document.createElement('h5');
        title.textContent = behavior.name;

        const details = document.createElement('p');
        if (behavior.detected) {
            details.innerHTML = `
                <strong>Detected:</strong> Yes<br>
                <strong>Confidence:</strong> ${behavior.confidence}%<br>
                <strong>Duration:</strong> ${behavior.duration}s
            `;
        } else {
            details.innerHTML = `
                <strong>Detected:</strong> No<br>
                <strong>Confidence:</strong> ${behavior.confidence}%<br>
                <strong>Duration:</strong> 0s
            `;
        }

        content.appendChild(title);
        content.appendChild(details);

        card.appendChild(icon);
        card.appendChild(content);

        uploadElements.behaviorsGrid.appendChild(card);
    });
}

function cancelAnalysis() {
    state.isAnalyzing = false;
    uploadElements.progressFill.style.width = '0%';
    uploadElements.progressText.textContent = 'Analysis cancelled';

    // Reset to upload state
    setTimeout(() => {
        uploadElements.dropArea.style.display = 'flex';
        uploadElements.analyzeBtn.style.display = 'block';
        uploadElements.cancelBtn.style.display = 'none';
        uploadElements.progressSection.style.display = 'none';
        uploadElements.resultsSection.style.display = 'none';
    }, 2000);
}

function resetUploadScreen() {
    // Reset upload elements
    uploadElements.fileInput.value = '';
    uploadElements.analyzeBtn.disabled = true;
    uploadElements.cancelBtn.disabled = true;
    uploadElements.dropArea.style.display = 'flex';
    uploadElements.analyzeBtn.style.display = 'block';
    uploadElements.cancelBtn.style.display = 'none';
    uploadElements.progressSection.style.display = 'none';
    uploadElements.resultsSection.style.display = 'none';

    // Reset drop area content
    const uploadContent = uploadElements.dropArea.querySelector('.upload-content');
    uploadContent.innerHTML = `
        <div class="upload-icon">📁</div>
        <h3>Upload Video for Analysis</h3>
        <p>Drag and drop your video file here or click to browse</p>
        <input type="file" id="file-input" accept="video/*" style="display: none;">
        <button class="browse-btn" onclick="document.getElementById('file-input').click()">Browse Files</button>
    `;

    // Clear state
    state.selectedFile = null;
    state.isAnalyzing = false;
    state.currentAnalysis = null;
}

// Reports Functions
function saveReport(results) {
    const report = {
        id: Date.now().toString(),
        fileName: results.fileName,
        fileSize: results.fileSize,
        overallAssessment: results.overallAssessment,
        confidenceScore: results.confidenceScore,
        detectedCount: results.detectedCount,
        timestamp: results.timestamp,
        behaviors: results.behaviors
    };

    state.reports.unshift(report);
    saveReportsToStorage();
    showNotification('Report saved successfully', 'success');
}

function loadReports() {
    const saved = localStorage.getItem('early_screen_asd_reports');
    if (saved) {
        try {
            state.reports = JSON.parse(saved);
        } catch (e) {
            console.error('Error loading reports:', e);
            state.reports = [];
        }
    }
}

function saveReportsToStorage() {
    localStorage.setItem('early_screen_asd_reports', JSON.stringify(state.reports));
}

function renderReports() {
    const list = reportsElements.reportsList;

    if (state.reports.length === 0) {
        list.innerHTML = `
            <div class="no-reports">
                <div class="no-reports-icon">📋</div>
                <p>No analysis reports yet. Upload a video to get started.</p>
            </div>
        `;
        return;
    }

    list.innerHTML = '';

    state.reports.forEach(report => {
        const item = document.createElement('div');
        item.className = 'report-item';
        item.onclick = () => showReportDetails(report);

        const header = document.createElement('div');
        header.className = 'report-header';

        const title = document.createElement('div');
        title.className = 'report-title';
        title.textContent = report.fileName;

        const date = document.createElement('div');
        date.className = 'report-date';
        date.textContent = new Date(report.timestamp).toLocaleString();

        header.appendChild(title);
        header.appendChild(date);

        const summary = document.createElement('div');
        summary.className = 'report-summary';

        const assessmentMetric = document.createElement('div');
        assessmentMetric.className = 'report-metric';
        assessmentMetric.innerHTML = `
            <div class="report-metric-label">Assessment</div>
            <div class="report-metric-value">${report.overallAssessment}</div>
        `;

        const confidenceMetric = document.createElement('div');
        confidenceMetric.className = 'report-metric';
        confidenceMetric.innerHTML = `
            <div class="report-metric-label">Confidence</div>
            <div class="report-metric-value">${report.confidenceScore}%</div>
        `;

        const behaviorsMetric = document.createElement('div');
        behaviorsMetric.className = 'report-metric';
        behaviorsMetric.innerHTML = `
            <div class="report-metric-label">Behaviors</div>
            <div class="report-metric-value">${report.detectedCount}</div>
        `;

        summary.appendChild(assessmentMetric);
        summary.appendChild(confidenceMetric);
        summary.appendChild(behaviorsMetric);

        item.appendChild(header);
        item.appendChild(summary);

        list.appendChild(item);
    });
}

function showReportDetails(report) {
    // This would show a detailed view of the report
    // For now, we'll navigate to upload screen and display the results
    navigateTo('upload-screen');

    // Simulate loading the report data
    uploadElements.overallAssessment.textContent = report.overallAssessment;
    uploadElements.confidenceScore.textContent = `${report.confidenceScore}%`;
    uploadElements.analysisTime.textContent = 'Report loaded';
    uploadElements.analysisTimestamp.textContent = new Date(report.timestamp).toLocaleString();

    // Set colors based on assessment
    const assessmentElement = uploadElements.overallAssessment;
    assessmentElement.className = 'result-value';
    if (report.overallAssessment.includes('Low')) {
        assessmentElement.style.color = '#10b981'; // Green
    } else if (report.overallAssessment.includes('Moderate')) {
        assessmentElement.style.color = '#f59e0b'; // Orange
    } else {
        assessmentElement.style.color = '#ef4444'; // Red
    }

    // Render behavior details
    renderBehaviors(report.behaviors);

    // Show results section
    uploadElements.progressSection.style.display = 'none';
    uploadElements.resultsSection.style.display = 'flex';
}

// Search Functionality
reportsElements.searchInput.addEventListener('input', function (e) {
    const query = e.target.value.toLowerCase();

    if (!query) {
        renderReports();
        return;
    }

    const filteredReports = state.reports.filter(report =>
        report.fileName.toLowerCase().includes(query) ||
        new Date(report.timestamp).toLocaleDateString().includes(query)
    );

    // Temporarily replace reports for rendering
    const originalReports = [...state.reports];
    state.reports = filteredReports;
    renderReports();

    // Restore original reports after a short delay
    setTimeout(() => {
        state.reports = originalReports;
    }, 100);
});

// Utility Functions
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    // Add to body
    document.body.appendChild(notification);

    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Keyboard Navigation Support
document.addEventListener('keydown', function (e) {
    // TV remote navigation support
    if (e.key === 'Enter') {
        const focusedElement = document.activeElement;
        if (focusedElement && focusedElement.tagName === 'BUTTON') {
            focusedElement.click();
        }
    }
});

// Touch Support for Mobile/TV
document.addEventListener('touchstart', function (e) {
    const target = e.target;
    if (target && target.classList.contains('nav-button')) {
        target.style.transform = 'scale(0.95)';
        setTimeout(() => {
            target.style.transform = '';
        }, 150);
    }
}, { passive: true });

// Initialize event listeners
function initializeEventListeners() {
    // File input change listener
    uploadElements.fileInput.addEventListener('change', function (e) {
        if (this.files && this.files.length > 0) {
            handleFiles(this.files);
        }
    });

    // Analyze button click
    uploadElements.analyzeBtn.addEventListener('click', startAnalysis);

    // Cancel button click
    uploadElements.cancelBtn.addEventListener('click', cancelAnalysis);

    // Search input
    reportsElements.searchInput.addEventListener('input', function (e) {
        const query = e.target.value.toLowerCase();

        if (!query) {
            renderReports();
            return;
        }

        const filteredReports = state.reports.filter(report =>
            report.fileName.toLowerCase().includes(query) ||
            new Date(report.timestamp).toLocaleDateString().includes(query)
        );

        // Temporarily replace reports for rendering
        const originalReports = [...state.reports];
        state.reports = filteredReports;
        renderReports();

        // Restore original reports after a short delay
        setTimeout(() => {
            state.reports = originalReports;
        }, 100);
    });
}