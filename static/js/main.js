// Main JavaScript for GestureDrive

// Check system status when page loads
document.addEventListener('DOMContentLoaded', function() {
    checkSystemStatus();
});

// Function to check system status
function checkSystemStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            console.log('System status:', data);
            if (data.status === 'online') {
                console.log('GestureDrive system is online');
            }
        })
        .catch(error => {
            console.error('Error checking system status:', error);
        });
}