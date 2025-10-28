// Main JavaScript functionality for HarkOnReddit
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize event listeners
    setupTimeFilters();
    setupAutoRefresh();
    setupModalHandlers();
    
    // Start periodic updates
    updateTimestamps();
    setInterval(updateTimestamps, 60000); // Update every minute
}

// Time filter functionality
function setupTimeFilters() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            filterButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Get selected time period
            const hours = this.getAttribute('data-hours');
            
            // Refresh data with new filter
            refreshDataWithFilter(hours);
        });
    });
}

// Auto-refresh functionality
function setupAutoRefresh() {
    // Auto-refresh every 5 minutes
    setInterval(() => {
        refreshData(true); // Silent refresh
    }, 300000);
}

// Modal handlers
function setupModalHandlers() {
    // Close modal when clicking outside - use proper close function
    window.addEventListener('click', function(event) {
        if (event.target.classList.contains('modal')) {
            const modalId = event.target.id;
            if (modalId) {
                closeModal(modalId);
            } else {
                closeAllModals();
            }
        }
    });
    
    // Close modal with Escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            closeAllModals();
        }
    });
}

// Refresh data functionality
function refreshData(silent = false) {
    if (!silent) {
        showLoadingOverlay();
    }
    
    fetch('/api/refresh')
        .then(response => response.json())
        .then(data => {
            if (!silent) {
                // Show success message
                showFlashMessage('Data refreshed successfully!', 'success');
                
                // Reload the page to show new data
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            }
        })
        .catch(error => {
            console.error('Error refreshing data:', error);
            if (!silent) {
                showFlashMessage('Error refreshing data. Please try again.', 'error');
            }
        })
        .finally(() => {
            if (!silent) {
                hideLoadingOverlay();
            }
        });
}

// Refresh data with time filter
function refreshDataWithFilter(hours) {
    showLoadingOverlay();
    
    fetch(`/api/stocks?hours=${hours}`)
        .then(response => response.json())
        .then(data => {
            updateStocksDisplay(data);
            showFlashMessage(`Updated to show data from last ${hours} hour${hours > 1 ? 's' : ''}`, 'success');
        })
        .catch(error => {
            console.error('Error filtering data:', error);
            showFlashMessage('Error filtering data. Please try again.', 'error');
        })
        .finally(() => {
            hideLoadingOverlay();
        });
}

// Update stocks display
function updateStocksDisplay(stocks) {
    const stocksGrid = document.querySelector('.stocks-grid');
    if (!stocksGrid) return;
    
    if (stocks.length === 0) {
        stocksGrid.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">
                    <i class="fas fa-chart-line"></i>
                </div>
                <h3>No Stock Data Available</h3>
                <p>No stocks found for the selected time period.</p>
            </div>
        `;
        return;
    }
    
    stocksGrid.innerHTML = stocks.map(stock => createStockCard(stock)).join('');
}

// Create stock card HTML
function createStockCard(stock) {
    const sentimentIcon = stock.overall_sentiment === 'bullish' ? 'arrow-up' : 
                         stock.overall_sentiment === 'bearish' ? 'arrow-down' : 'minus';
    
    return `
        <div class="stock-card" data-symbol="${stock.symbol}">
            <div class="stock-header">
                <div class="stock-symbol">
                    <h3>$${stock.symbol}</h3>
                    <div class="stock-badges">
                        <span class="mentions-badge">
                            <i class="fas fa-comment"></i>
                            ${stock.mentions}
                        </span>
                    </div>
                </div>
                <div class="sentiment-indicator sentiment-${stock.overall_sentiment}">
                    <i class="fas fa-${sentimentIcon}"></i>
                    <span>${stock.overall_sentiment.charAt(0).toUpperCase() + stock.overall_sentiment.slice(1)}</span>
                </div>
            </div>
            
            <div class="stock-metrics">
                <div class="metric">
                    <span class="metric-label">Sentiment Score</span>
                    <span class="metric-value sentiment-score sentiment-${stock.overall_sentiment}">
                        ${stock.avg_sentiment.toFixed(3)}
                    </span>
                </div>
                <div class="metric">
                    <span class="metric-label">Unique Posts</span>
                    <span class="metric-value">${stock.unique_posts}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Confidence</span>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${Math.round(stock.sentiment_strength * 100)}%"></div>
                    </div>
                </div>
            </div>
            
            <div class="stock-footer">
                <div class="last-mention">
                    <i class="fas fa-clock"></i>
                    Latest: ${formatTimestamp(stock.latest_mention)}
                </div>
                <button class="view-details-btn" onclick="viewStockDetails('${stock.symbol}')">
                    <i class="fas fa-external-link-alt"></i>
                    Details
                </button>
            </div>
        </div>
    `;
}

// Format timestamp for display
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMinutes = Math.floor(diffMs / 60000);
    
    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
}

// Update timestamps
function updateTimestamps() {
    const timestampElements = document.querySelectorAll('[data-timestamp]');
    timestampElements.forEach(element => {
        const timestamp = element.getAttribute('data-timestamp');
        element.textContent = formatTimestamp(timestamp);
    });
    
    // Update last updated time
    const lastUpdatedElement = document.getElementById('last-updated-time');
    if (lastUpdatedElement) {
        lastUpdatedElement.textContent = new Date().toLocaleTimeString([], {
            hour: '2-digit', 
            minute: '2-digit'
        });
    }
}

// Show loading overlay
function showLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'flex';
    }
}

// Hide loading overlay
function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

// Show flash message
function showFlashMessage(message, type = 'success') {
    const flashContainer = document.querySelector('.flash-messages') || createFlashContainer();
    
    const flashMessage = document.createElement('div');
    flashMessage.className = `flash-message flash-${type}`;
    flashMessage.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'}"></i>
        ${message}
        <button class="flash-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    flashContainer.appendChild(flashMessage);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (flashMessage.parentNode) {
            flashMessage.remove();
        }
    }, 5000);
}

// Create flash container if it doesn't exist
function createFlashContainer() {
    const container = document.createElement('div');
    container.className = 'flash-messages';
    document.body.appendChild(container);
    return container;
}

// Modal functions
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        console.log(`Opening modal: ${modalId}`);
        
        // Calculate scrollbar width to prevent content shift
        const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
        
        // Store original body styles
        const originalOverflow = document.body.style.overflow;
        const originalPaddingRight = document.body.style.paddingRight;
        
        // Store these for later restoration
        modal.dataset.originalOverflow = originalOverflow;
        modal.dataset.originalPaddingRight = originalPaddingRight;
        
        // Prevent scrolling and compensate for scrollbar
        document.body.style.overflow = 'hidden';
        document.body.style.paddingRight = scrollbarWidth + 'px';
        
        modal.style.display = 'block';
        
        // Add slight delay for smooth appearance
        setTimeout(() => {
            modal.style.opacity = '1';
        }, 10);
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        console.log(`Closing modal: ${modalId}`);
        
        // Add fade out animation
        modal.style.opacity = '0';
        
        // Restore original body styles immediately (prevent shift back)
        const originalOverflow = modal.dataset.originalOverflow || 'auto';
        const originalPaddingRight = modal.dataset.originalPaddingRight || '';
        
        document.body.style.overflow = originalOverflow;
        document.body.style.paddingRight = originalPaddingRight;
        
        // Wait for animation, then hide
        setTimeout(() => {
            modal.style.display = 'none';
            modal.style.opacity = '1'; // Reset for next time
            
            // Clean up stored data
            delete modal.dataset.originalOverflow;
            delete modal.dataset.originalPaddingRight;
        }, 200);
        
        // Clear any loading states or content if it's the stock details modal
        if (modalId === 'stock-details-modal') {
            const content = document.getElementById('stock-details-content');
            if (content) {
                // Clear any pending fetch requests by adding a small delay
                setTimeout(() => {
                    if (modal.style.display === 'none') {
                        content.innerHTML = '';
                    }
                }, 300);
            }
        }
    }
}

function closeAllModals() {
    console.log('Closing all modals');
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        const modalId = modal.id;
        if (modalId) {
            closeModal(modalId);
        } else {
            modal.style.display = 'none';
        }
    });
    
    // Fallback restoration in case any modal didn't restore properly
    document.body.style.overflow = 'auto';
    document.body.style.paddingRight = '';
}

// Show About modal
function showAbout() {
    showModal('about-modal');
}

// Show Disclaimer modal
function showDisclaimer() {
    showModal('disclaimer-modal');
}

// View stock details - REAL API VERSION
function viewStockDetails(symbol) {
    showModal('stock-details-modal');
    
    // Show loading state
    const content = document.getElementById('stock-details-content');
    if (content) {
        content.innerHTML = `
            <div class="loading-state">
                <i class="fas fa-spinner fa-spin"></i>
                <h2>Loading ${symbol} Details...</h2>
                <p>Fetching real data from /api/stock/${symbol}...</p>
            </div>
        `;
    }
    
    console.log(`Fetching details for stock: ${symbol}`);
    
    // Fetch REAL stock data from API
    fetch(`/api/stock/${symbol}`)
        .then(response => {
            console.log(`API Response status: ${response.status}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Stock details received:', data);
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            const info = data.basic_info;
            const sentimentClass = info.overall_sentiment;
            const sentimentIcon = info.overall_sentiment === 'bullish' ? 'arrow-up' : 
                                info.overall_sentiment === 'bearish' ? 'arrow-down' : 'minus';
            
            content.innerHTML = `
                <div class="stock-details-header">
                    <h2>
                        $${data.symbol} 
                        <span class="sentiment-badge sentiment-${sentimentClass}">
                            <i class="fas fa-${sentimentIcon}"></i>
                            ${info.overall_sentiment.toUpperCase()}
                        </span>
                    </h2>
                </div>

                <div class="details-metrics">
                    <div class="metric-card">
                        <h3><i class="fas fa-comments"></i> Total Mentions</h3>
                        <div class="metric-number">${info.mentions}</div>
                    </div>
                    <div class="metric-card">
                        <h3><i class="fas fa-brain"></i> Avg Sentiment</h3>
                        <div class="metric-number sentiment-${sentimentClass}">${info.avg_sentiment >= 0 ? '+' : ''}${info.avg_sentiment}</div>
                    </div>
                    <div class="metric-card">
                        <h3><i class="fas fa-chart-pie"></i> Sentiment Breakdown</h3>
                        <div class="sentiment-breakdown">
                            <div class="sentiment-percentages">
                                <div class="percentage-item">
                                    <span class="percentage-color bullish-color"></span>
                                    <span>Bullish: ${(info.bullish/info.mentions*100).toFixed(1)}%</span>
                                </div>
                                <div class="percentage-item">
                                    <span class="percentage-color neutral-color"></span>
                                    <span>Neutral: ${(info.neutral/info.mentions*100).toFixed(1)}%</span>
                                </div>
                                <div class="percentage-item">
                                    <span class="percentage-color bearish-color"></span>
                                    <span>Bearish: ${(info.bearish/info.mentions*100).toFixed(1)}%</span>
                                </div>
                            </div>
                            <div class="sentiment-bar">
                                <div class="bullish" style="width: ${(info.bullish/info.mentions*100).toFixed(1)}%" title="Bullish: ${info.bullish} mentions (${(info.bullish/info.mentions*100).toFixed(1)}%)">${info.bullish > 0 ? info.bullish : ''}</div>
                                <div class="neutral" style="width: ${(info.neutral/info.mentions*100).toFixed(1)}%" title="Neutral: ${info.neutral} mentions (${(info.neutral/info.mentions*100).toFixed(1)}%)">${info.neutral > 0 ? info.neutral : ''}</div>
                                <div class="bearish" style="width: ${(info.bearish/info.mentions*100).toFixed(1)}%" title="Bearish: ${info.bearish} mentions (${(info.bearish/info.mentions*100).toFixed(1)}%)">${info.bearish > 0 ? info.bearish : ''}</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="details-section">
                    <h3><i class="fas fa-history"></i> Recent Mentions</h3>
                    <div class="mentions-list">
                        ${data.recent_mentions.map(mention => `
                            <div class="mention-item">
                                <div class="mention-header">
                                    <span class="mention-source">${mention.source.replace('reddit/r/', 'r/')}</span>
                                    <span class="mention-time">${formatTimeAgoFromTimestamp(mention.timestamp)}</span>
                                    <span class="mention-sentiment sentiment-${mention.sentiment_label}">
                                        ${mention.sentiment >= 0 ? '+' : ''}${mention.sentiment}
                                    </span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>

                ${data.top_sources.length > 0 ? `
                <div class="details-section">
                    <h3><i class="fas fa-reddit"></i> Top Sources</h3>
                    <div class="sources-list">
                        ${data.top_sources.map(source => `
                            <div class="source-item">
                                <span class="source-name">${source.source.replace('reddit/r/', 'r/')}</span>
                                <span class="source-mentions">${source.mentions} mentions</span>
                                <span class="source-sentiment sentiment-${source.avg_sentiment > 0.1 ? 'bullish' : source.avg_sentiment < -0.1 ? 'bearish' : 'neutral'}">
                                    ${source.avg_sentiment >= 0 ? '+' : ''}${source.avg_sentiment}
                                </span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
                
                <div class="detail-actions">
                    <button class="action-btn" onclick="window.open('https://finance.yahoo.com/quote/${symbol}', '_blank')">
                        <i class="fas fa-external-link-alt"></i>
                        View on Yahoo Finance
                    </button>

                </div>
            `;
        })
        .catch(error => {
            console.error('Error fetching stock details:', error);
            content.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h2>Error Loading ${symbol}</h2>
                    <p><strong>Error:</strong> ${error.message}</p>
                    <p><strong>API Endpoint:</strong> /api/stock/${symbol}</p>
                    <div class="error-details">
                        <p>Possible causes:</p>
                        <ul>
                            <li>Flask app not running</li>
                            <li>Stock ${symbol} not found in database</li>
                            <li>Database connection issue</li>
                            <li>API endpoint error</li>
                        </ul>
                    </div>
                    <button onclick="viewStockDetails('${symbol}')" class="retry-btn">
                        <i class="fas fa-redo"></i> Try Again
                    </button>
                    <button onclick="checkApiStatus()" class="debug-btn">
                        <i class="fas fa-bug"></i> Check API Status
                    </button>
                </div>
            `;
        });
}

// Helper function for time formatting in stock details
function formatTimeAgoFromTimestamp(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMinutes = Math.floor((now - time) / (1000 * 60));
    
    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h ago`;
    return `${Math.floor(diffMinutes / 1440)}d ago`;
}

// API Status Check function
function checkApiStatus() {
    console.log('Checking API status...');
    
    const content = document.getElementById('stock-details-content');
    content.innerHTML = `
        <div class="loading-state">
            <i class="fas fa-spinner fa-spin"></i>
            <h2>Checking API Status...</h2>
        </div>
    `;
    
    // Test basic API endpoints
    Promise.all([
        fetch('/api/stocks').then(r => ({endpoint: '/api/stocks', status: r.status, ok: r.ok})).catch(e => ({endpoint: '/api/stocks', status: 'ERROR', ok: false, error: e.message})),
        fetch('/api/status').then(r => ({endpoint: '/api/status', status: r.status, ok: r.ok})).catch(e => ({endpoint: '/api/status', status: 'ERROR', ok: false, error: e.message}))
    ]).then(results => {
        console.log('API Status Results:', results);
        
        const statusHtml = results.map(result => 
            `<li>${result.endpoint}: ${result.ok ? '✅' : '❌'} ${result.status} ${result.error ? '(' + result.error + ')' : ''}</li>`
        ).join('');
        
        content.innerHTML = `
            <div class="debug-info">
                <h2><i class="fas fa-bug"></i> API Status Check</h2>
                <ul>${statusHtml}</ul>
                <button onclick="testStockApi()" class="debug-btn">Test Stock API</button>
                <button onclick="closeModal('stock-details-modal')" class="close-btn">Close</button>
            </div>
        `;
    }).catch(error => {
        console.error('API status check failed:', error);
        content.innerHTML = `
            <div class="error-state">
                <h2>API Connection Failed</h2>
                <p>Cannot connect to Flask server. Make sure the app is running:</p>
                <code>python app.py</code>
                <p><strong>Error:</strong> ${error.message}</p>
                <button onclick="closeModal('stock-details-modal')" class="close-btn">Close</button>
            </div>
        `;
    });
}

// Test Stock API function
function testStockApi() {
    const content = document.getElementById('stock-details-content');
    
    // Test with known stocks from the database
    const testStocks = ['BYND', 'CAN', 'ANY', 'TECH', 'META', 'NVDA'];
    
    console.log('Testing stock API with known symbols...');
    
    content.innerHTML = `
        <div class="loading-state">
            <i class="fas fa-spinner fa-spin"></i>
            <h2>Testing Stock API...</h2>
            <p>Testing with: ${testStocks.join(', ')}</p>
        </div>
    `;
    
    Promise.all(testStocks.map(symbol => 
        fetch(`/api/stock/${symbol}`)
            .then(r => r.json())
            .then(data => ({symbol, success: true, data}))
            .catch(error => ({symbol, success: false, error: error.message}))
    )).then(results => {
        let testHtml = '<h3>Stock API Tests:</h3><ul>';
        
        results.forEach(result => {
            if (result.success && !result.data.error) {
                testHtml += `<li>✅ ${result.symbol}: ${result.data.basic_info?.mentions || 0} mentions</li>`;
            } else {
                const errorMsg = result.data?.error || result.error || 'Unknown error';
                testHtml += `<li>❌ ${result.symbol}: ${errorMsg}</li>`;
            }
        });
        
        testHtml += '</ul>';
        
        content.innerHTML = `
            <div class="debug-info">
                <h2>Stock API Test Results</h2>
                ${testHtml}
                <button onclick="closeModal('stock-details-modal')" class="close-btn">Close</button>
            </div>
        `;
    });
}



// Form validation and enhancement
function setupFormEnhancements() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            const emailInput = form.querySelector('input[type="email"]');
            
            if (emailInput && !isValidEmail(emailInput.value)) {
                event.preventDefault();
                showFlashMessage('Please enter a valid email address.', 'error');
                emailInput.focus();
                return false;
            }
            
            // Show loading state
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            }
        });
    });
}

// Email validation
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Initialize form enhancements when page loads
document.addEventListener('DOMContentLoaded', function() {
    setupFormEnhancements();
});

// Add smooth scrolling for anchor links
document.addEventListener('DOMContentLoaded', function() {
    const links = document.querySelectorAll('a[href^="#"]');
    
    links.forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();
            
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

// Add keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + R to refresh data
    if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
        event.preventDefault();
        refreshData();
    }
    
    // Escape to close modals
    if (event.key === 'Escape') {
        closeAllModals();
    }
});

// Add animation classes when elements come into view
function setupScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    // Observe stock cards
    document.querySelectorAll('.stock-card').forEach(card => {
        observer.observe(card);
    });
    
    // Observe other elements
    document.querySelectorAll('.criteria-item, .subscribe-card').forEach(element => {
        observer.observe(element);
    });
}

// Initialize scroll animations
document.addEventListener('DOMContentLoaded', function() {
    setupScrollAnimations();
});

// Add CSS animation class
const style = document.createElement('style');
style.textContent = `
    .animate-in {
        animation: slideUp 0.6s ease forwards;
    }
    
    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;
document.head.appendChild(style);