document.addEventListener('DOMContentLoaded', function() {
    // Load the initial configuration
    loadGestureConfiguration();

    // Set up event handlers
    document.getElementById('reload-config').addEventListener('click', reloadConfiguration);
    document.getElementById('edit-config').addEventListener('click', enableConfigEditor);
    document.getElementById('cancel-edit').addEventListener('click', disableConfigEditor);
    document.getElementById('save-config').addEventListener('click', saveConfiguration);
    
    // Context selector handling
    document.getElementById('context-selector').addEventListener('click', function(event) {
        if (event.target.hasAttribute('data-context')) {
            setGestureContext(event.target.getAttribute('data-context'));
        }
    });
});

/**
 * Loads the gesture configuration from the server
 */
function loadGestureConfiguration() {
    fetch('/api/gestures/config')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updateConfigurationUI(data);
        })
        .catch(error => {
            showStatusMessage('error', 'Failed to load configuration: ' + error.message);
        });
}

/**
 * Reloads the gesture configuration from disk
 */
function reloadConfiguration() {
    const button = document.getElementById('reload-config');
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>Reloading...';

fetch('/api/gestures/reload', {
    method: 'POST'
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        showStatusMessage('success', 'Configuration reloaded successfully');
        // Refresh the configuration display
        loadGestureConfiguration();
    } else {
        showStatusMessage('error', 'Failed to reload configuration');
    }
})
.catch(error => {
    showStatusMessage('error', 'Error: ' + error.message);
})
.finally(() => {
    button.disabled = false;
    button.innerHTML = '<i class="fas fa-sync-alt"></i>Reload Configuration';
});
}