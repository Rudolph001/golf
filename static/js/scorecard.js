// Golf Tournament Scorecard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize scorecard functionality
    initializeScorecard();
    
    // Auto-calculate totals when scores change
    const scoreInputs = document.querySelectorAll('.score-input');
    scoreInputs.forEach(input => {
        input.addEventListener('input', calculateTotals);
        input.addEventListener('change', validateScore);
    });
});

function initializeScorecard() {
    // Calculate initial totals if scores exist
    calculateTotals();
    
    // Set up mobile-friendly input handling
    const scoreInputs = document.querySelectorAll('.score-input');
    scoreInputs.forEach(input => {
        // Select all text when focused for easy editing
        input.addEventListener('focus', function() {
            this.select();
        });
        
        // Handle mobile keyboard
        input.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                const nextInput = getNextInput(this);
                if (nextInput) {
                    nextInput.focus();
                }
            }
        });
    });
}

function calculateTotals() {
    let frontNine = 0;
    let backNine = 0;
    let frontCount = 0;
    let backCount = 0;
    
    // Calculate front nine (holes 1-9)
    for (let i = 1; i <= 9; i++) {
        const input = document.querySelector(`input[name="hole_${i}"]`);
        if (input && input.value && !isNaN(input.value)) {
            frontNine += parseInt(input.value);
            frontCount++;
        }
    }
    
    // Calculate back nine (holes 10-18)
    for (let i = 10; i <= 18; i++) {
        const input = document.querySelector(`input[name="hole_${i}"]`);
        if (input && input.value && !isNaN(input.value)) {
            backNine += parseInt(input.value);
            backCount++;
        }
    }
    
    // Update front nine total
    const frontTotal = document.getElementById('front-total');
    if (frontTotal) {
        frontTotal.textContent = frontCount > 0 ? frontNine : '-';
    }
    
    // Update back nine total
    const backTotal = document.getElementById('back-total');
    if (backTotal) {
        backTotal.textContent = backCount > 0 ? backNine : '-';
    }
    
    // Update overall totals
    const totalStrokes = frontNine + backNine;
    const totalStrokesElement = document.getElementById('total-strokes');
    if (totalStrokesElement && (frontCount > 0 || backCount > 0)) {
        totalStrokesElement.textContent = totalStrokes;
    }
    
    // Calculate score to par
    const scoreToParElement = document.getElementById('score-to-par');
    if (scoreToParElement && totalStrokes > 0) {
        const par = 72; // Course par
        const diff = totalStrokes - par;
        if (diff > 0) {
            scoreToParElement.textContent = `+${diff}`;
            scoreToParElement.className = 'text-danger mb-1';
        } else if (diff < 0) {
            scoreToParElement.textContent = diff.toString();
            scoreToParElement.className = 'text-success mb-1';
        } else {
            scoreToParElement.textContent = 'E';
            scoreToParElement.className = 'text-info mb-1';
        }
    }
    
    // Calculate Stableford points (using actual par values)
    const stablefordElement = document.getElementById('stableford-points');
    if (stablefordElement && totalStrokes > 0) {
        let stablefordPoints = 0;
        
        // Par values for each hole based on Pinaclepoint course
        const parValues = [4,4,4,4,5,4,3,4,3,4,4,4,3,4,4,5,3,5];
        
        for (let i = 1; i <= 18; i++) {
            const input = document.querySelector(`input[name="hole_${i}"]`);
            if (input && input.value && !isNaN(input.value)) {
                const score = parseInt(input.value);
                const par = parValues[i-1];
                // Stableford points: Eagle=4, Birdie=3, Par=2, Bogey=1, Double bogey or worse=0
                if (score <= par - 2) {
                    stablefordPoints += 4; // Eagle or better
                } else if (score === par - 1) {
                    stablefordPoints += 3; // Birdie
                } else if (score === par) {
                    stablefordPoints += 2; // Par
                } else if (score === par + 1) {
                    stablefordPoints += 1; // Bogey
                }
                // Double bogey or worse = 0 points (no addition needed)
            }
        }
        
        stablefordElement.textContent = stablefordPoints;
    }
}

function validateScore(event) {
    const input = event.target;
    const value = parseInt(input.value);
    
    // Validate score is reasonable (1-12 strokes per hole)
    if (value < 1 || value > 12) {
        input.classList.add('is-invalid');
        showTooltip(input, 'Score must be between 1 and 12');
    } else {
        input.classList.remove('is-invalid');
        hideTooltip(input);
        
        // Add visual feedback for special scores using actual par values
        const parValues = [4,4,4,4,5,4,3,4,3,4,4,4,3,4,4,5,3,5];
        const holeNumber = parseInt(input.name.replace('hole_', ''));
        const par = parValues[holeNumber - 1];
        
        input.classList.remove('birdie', 'eagle', 'bogey', 'double-bogey');
        
        if (value <= par - 2) {
            input.classList.add('eagle');
            input.style.backgroundColor = '#d4edda';
        } else if (value === par - 1) {
            input.classList.add('birdie');
            input.style.backgroundColor = '#d1ecf1';
        } else if (value === par + 1) {
            input.classList.add('bogey');
            input.style.backgroundColor = '#fff3cd';
        } else if (value >= par + 2) {
            input.classList.add('double-bogey');
            input.style.backgroundColor = '#f8d7da';
        } else {
            input.style.backgroundColor = '';
        }
    }
}

function getNextInput(currentInput) {
    const allInputs = Array.from(document.querySelectorAll('.score-input'));
    const currentIndex = allInputs.indexOf(currentInput);
    return allInputs[currentIndex + 1] || null;
}

function showTooltip(element, message) {
    // Create or update tooltip
    let tooltip = element.nextElementSibling;
    if (!tooltip || !tooltip.classList.contains('invalid-feedback')) {
        tooltip = document.createElement('div');
        tooltip.className = 'invalid-feedback';
        element.parentNode.insertBefore(tooltip, element.nextSibling);
    }
    tooltip.textContent = message;
    tooltip.style.display = 'block';
}

function hideTooltip(element) {
    const tooltip = element.nextElementSibling;
    if (tooltip && tooltip.classList.contains('invalid-feedback')) {
        tooltip.style.display = 'none';
    }
}

// Auto-save functionality (optional)
function autoSave() {
    const form = document.querySelector('form');
    if (form) {
        const formData = new FormData(form);
        
        // Save to localStorage as backup
        const scoreData = {};
        for (let [key, value] of formData.entries()) {
            if (key.startsWith('hole_') && value) {
                scoreData[key] = value;
            }
        }
        
        const scoreId = formData.get('score_id');
        if (scoreId) {
            localStorage.setItem(`scorecard_${scoreId}`, JSON.stringify(scoreData));
        }
    }
}

// Load saved data on page load
function loadSavedData() {
    const scoreIdInput = document.querySelector('input[name="score_id"]');
    if (scoreIdInput) {
        const scoreId = scoreIdInput.value;
        const savedData = localStorage.getItem(`scorecard_${scoreId}`);
        
        if (savedData) {
            try {
                const data = JSON.parse(savedData);
                for (let [key, value] of Object.entries(data)) {
                    const input = document.querySelector(`input[name="${key}"]`);
                    if (input && !input.value) {
                        input.value = value;
                    }
                }
                calculateTotals();
            } catch (e) {
                console.log('Error loading saved data:', e);
            }
        }
    }
}

// Keyboard shortcuts for common scores
document.addEventListener('keydown', function(e) {
    const activeElement = document.activeElement;
    
    if (activeElement && activeElement.classList.contains('score-input')) {
        // Quick entry shortcuts
        switch(e.key) {
            case 'p': // Par (4)
            case 'P':
                e.preventDefault();
                activeElement.value = '4';
                activeElement.dispatchEvent(new Event('input'));
                break;
            case 'b': // Birdie (3)
            case 'B':
                e.preventDefault();
                activeElement.value = '3';
                activeElement.dispatchEvent(new Event('input'));
                break;
            case 'e': // Eagle (2)
            case 'E':
                e.preventDefault();
                activeElement.value = '2';
                activeElement.dispatchEvent(new Event('input'));
                break;
        }
    }
});

// Print scorecard functionality
function printScorecard() {
    window.print();
}

// Export scorecard data
function exportScorecard() {
    const scoreData = {};
    const inputs = document.querySelectorAll('.score-input');
    
    inputs.forEach(input => {
        if (input.value) {
            scoreData[input.name] = input.value;
        }
    });
    
    const dataStr = JSON.stringify(scoreData, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = 'scorecard.json';
    link.click();
}

// Tournament leaderboard updates
function refreshLeaderboard() {
    // This would typically make an AJAX call to update the leaderboard
    // For now, we'll just reload the page
    if (confirm('Refresh leaderboard with latest scores?')) {
        window.location.reload();
    }
}

// Touch-friendly mobile interactions
if ('ontouchstart' in window) {
    // Add touch-specific styles
    const style = document.createElement('style');
    style.textContent = `
        .score-input {
            font-size: 16px; /* Prevent iOS zoom */
            padding: 12px;
        }
        
        .btn {
            min-height: 44px; /* Touch target size */
        }
    `;
    document.head.appendChild(style);
}

// Initialize auto-save (save every 30 seconds)
setInterval(autoSave, 30000);

// Load any saved data when page loads
window.addEventListener('load', loadSavedData);
