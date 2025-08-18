// Modern Enhancements for Reveal.js Presentations

// Copy to Clipboard Functionality
function initCopyButtons() {
    // Add copy buttons to code blocks
    const codeBlocks = document.querySelectorAll('pre code');
    codeBlocks.forEach(block => {
        const pre = block.parentElement;
        if (!pre.querySelector('.copy-button') && !pre.closest('.terminal-block')) {
            const button = createCopyButton();
            pre.style.position = 'relative';
            pre.appendChild(button);
            
            button.addEventListener('click', () => {
                copyToClipboard(block.textContent, button);
            });
        }
    });

    // Add copy buttons to terminal windows (full copy)
    const terminalContents = document.querySelectorAll('.terminal-content, .vscode-terminal-content');
    terminalContents.forEach(terminal => {
        const parent = terminal.parentElement;
        if (!parent.querySelector('.copy-button') && !terminal.querySelector('.terminal-block')) {
            const button = createCopyButton();
            parent.style.position = 'relative';
            parent.appendChild(button);
            
            button.addEventListener('click', () => {
                const text = terminal.textContent || terminal.innerText;
                copyToClipboard(text, button);
            });
        }
    });

    // Add individual copy buttons for Warp-style terminal blocks
    const terminalBlocks = document.querySelectorAll('.terminal-block');
    terminalBlocks.forEach(block => {
        if (!block.querySelector('.copy-cmd')) {
            const button = document.createElement('button');
            button.className = 'copy-cmd';
            button.innerHTML = '<svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor"><path d="M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 010 1.5h-1.5a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-1.5a.75.75 0 011.5 0v1.5A1.75 1.75 0 019.25 16h-7.5A1.75 1.75 0 010 14.25v-7.5z"/><path d="M5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0114.25 11h-7.5A1.75 1.75 0 015 9.25v-7.5zm1.75-.25a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-7.5a.25.25 0 00-.25-.25h-7.5z"/></svg>';
            block.appendChild(button);
            
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const command = block.querySelector('.cmd-command');
                if (command) {
                    // Add rainbow border animation
                    block.classList.add('copying');
                    setTimeout(() => {
                        block.classList.remove('copying');
                    }, 800);
                    const originalIcon = button.innerHTML;
                    navigator.clipboard.writeText(command.textContent).then(() => {
                        button.innerHTML = '✅';
                        button.classList.add('copied');
                        
                        setTimeout(() => {
                            button.innerHTML = originalIcon;
                            button.classList.remove('copied');
                        }, 2000);
                    }).catch(err => {
                        console.error('Failed to copy:', err);
                        button.innerHTML = '❌';
                        setTimeout(() => {
                            button.innerHTML = originalIcon;
                        }, 2000);
                    });
                }
            });
        }
    });
}

function createCopyButton() {
    const button = document.createElement('button');
    button.className = 'copy-button';
    button.innerHTML = '📋 Copy';
    return button;
}

function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(() => {
        const originalText = button.innerHTML;
        button.innerHTML = '✅ Copied!';
        button.classList.add('copied');
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.classList.remove('copied');
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        button.innerHTML = '❌ Failed';
        setTimeout(() => {
            button.innerHTML = '📋 Copy';
        }, 2000);
    });
}

// Terminal Type Animation
function typeTerminalCommand(element, command, callback) {
    let i = 0;
    element.textContent = '';
    
    const typeChar = () => {
        if (i < command.length) {
            element.textContent += command[i];
            i++;
            setTimeout(typeChar, 50 + Math.random() * 50);
        } else if (callback) {
            setTimeout(callback, 500);
        }
    };
    
    typeChar();
}

// VSCode Tab Switching
function initVSCodeTabs() {
    const tabContainers = document.querySelectorAll('.vscode-tabs');
    
    tabContainers.forEach(container => {
        const tabs = container.querySelectorAll('.vscode-tab');
        const terminalContent = container.parentElement.querySelector('.vscode-terminal-content');
        
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Remove active class from all tabs
                tabs.forEach(t => t.classList.remove('active'));
                // Add active class to clicked tab
                tab.classList.add('active');
                
                // Hide all tab contents
                const allContents = terminalContent.querySelectorAll('.tab-content');
                allContents.forEach(content => {
                    content.style.display = 'none';
                });
                
                // Show the selected tab content
                const tabType = tab.dataset.tab;
                const selectedContent = terminalContent.querySelector(`#${tabType}-content`);
                if (selectedContent) {
                    selectedContent.style.display = 'block';
                }
            });
        });
    });
}

// Claude Response Animation
function animateClaudeResponse(element) {
    element.style.opacity = '0';
    element.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
        element.style.transition = 'all 0.5s ease-out';
        element.style.opacity = '1';
        element.style.transform = 'translateY(0)';
    }, 100);
}

// Code Comparison Tab Switching
function initCodeCompareTabs() {
    const compareContainers = document.querySelectorAll('.code-compare');
    
    compareContainers.forEach(container => {
        const tabs = container.querySelectorAll('.code-compare-tab');
        const beforeContent = container.querySelector('.code-before');
        const afterContent = container.querySelector('.code-after');
        
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Remove active class from all tabs and contents
                tabs.forEach(t => t.classList.remove('active'));
                beforeContent.classList.remove('active');
                afterContent.classList.remove('active');
                
                // Add active class to clicked tab
                tab.classList.add('active');
                
                // Show corresponding content
                if (tab.classList.contains('before')) {
                    beforeContent.classList.add('active');
                } else {
                    afterContent.classList.add('active');
                }
            });
        });
        
        // Set initial state (show "before" by default)
        if (tabs.length > 0 && beforeContent) {
            tabs[0].classList.add('active');
            beforeContent.classList.add('active');
        }
    });
}

// Initialize all enhancements when Reveal is ready
Reveal.on('ready', () => {
    initCopyButtons();
    initVSCodeTabs();
    
    // Re-initialize when slide changes (for dynamically loaded content)
    Reveal.on('slidechanged', () => {
        setTimeout(() => {
            initCopyButtons();
        }, 100);
    });
});

// Syntax highlighting for Claude prompts
hljs.registerLanguage('claude-prompt', function() {
    return {
        contains: [
            {
                className: 'keyword',
                begin: /^(Human|Assistant):/,
                relevance: 10
            },
            {
                className: 'string',
                begin: /"/, end: /"/,
                contains: [{begin: /\\./}]
            },
            {
                className: 'comment',
                begin: /#/, end: /$/
            }
        ]
    };
});

// Lazy loading for heavy resources
function lazyLoadCharts() {
    if (typeof Chart === 'undefined') {
        const script = document.createElement('script');
        script.src = 'engine/plugin/chart/chart.min.js';
        script.onload = () => {
            console.log('Chart.js loaded');
            // Trigger any pending chart initializations
            document.dispatchEvent(new Event('chartjs-loaded'));
        };
        document.head.appendChild(script);
    }
}

function lazyLoadMermaid() {
    const mermaidElements = document.querySelectorAll('.mermaid');
    if (mermaidElements.length > 0 && typeof mermaid === 'undefined') {
        const script = document.createElement('script');
        script.src = 'engine/plugin/mermaid/mermaid.js';
        script.onload = () => {
            mermaid.initialize({ 
                startOnLoad: true,
                theme: 'dark',
                themeVariables: {
                    darkMode: true,
                    background: '#0d1117',
                    primaryColor: '#58a6ff',
                    primaryTextColor: '#c9d1d9',
                    primaryBorderColor: '#30363d',
                    lineColor: '#8b949e',
                    secondaryColor: '#161b22',
                    tertiaryColor: '#21262d'
                }
            });
        };
        document.head.appendChild(script);
    }
}

// Check for charts and mermaid on slide change
Reveal.on('slidechanged', event => {
    const currentSlide = event.currentSlide;
    
    if (currentSlide.querySelector('[data-chart]')) {
        lazyLoadCharts();
    }
    
    if (currentSlide.querySelector('.mermaid')) {
        lazyLoadMermaid();
    }
});

// Keyboard shortcuts display
function showKeyboardShortcuts() {
    const shortcuts = {
        'Space': 'Next slide',
        'Shift+Space': 'Previous slide',
        'ESC': 'Overview mode',
        'F': 'Fullscreen',
        'S': 'Speaker notes',
        'B': 'Blackout',
        'Alt+Click': 'Zoom in'
    };
    
    let html = '<div style="padding: 20px;"><h3>Keyboard Shortcuts</h3><dl>';
    for (const [key, desc] of Object.entries(shortcuts)) {
        html += `<dt><span class="key-binding">${key}</span></dt><dd>${desc}</dd>`;
    }
    html += '</dl></div>';
    
    return html;
}

// Add custom key binding for help
Reveal.addKeyBinding({keyCode: 72, key: 'H', description: 'Show help'}, () => {
    alert('Help:\n\n' + Object.entries({
        'Space': 'Next slide',
        'Shift+Space': 'Previous slide',
        'ESC': 'Overview mode',
        'F': 'Fullscreen',
        'S': 'Speaker notes'
    }).map(([k,v]) => `${k}: ${v}`).join('\n'));
});