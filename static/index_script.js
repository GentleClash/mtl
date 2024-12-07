
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('importButton').addEventListener('click', handleFileImport);
});

// Handle file import
async function handleFileImport() {
    const fileInput = document.getElementById('file');
    const file = fileInput.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        if (response.redirected) {
            window.location.href = response.url;
        } else {
            const data = await response.json();
            if (data.success) {
                currentFile = data.filename;
                //Something to do i dont know what 
            }
        }
    } catch (error) {
        console.error('Error uploading file:', error);
    }
}
