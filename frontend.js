document.getElementById('uploadForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    
    const formData = new FormData();
    const videoFile = document.getElementById('videoFile').files[0];
    const videoURL = document.getElementById('videoURL').value;

    if (videoFile) {
        formData.append('file', videoFile);
    } else if (videoURL) {
        // Handle URL submission here if needed
        alert('URL submission not implemented yet.');
        return;
    } else {
        alert('Please upload a video file or enter a video URL.');
        return;
    }

    try {
        const response = await fetch('/transcribe/', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            throw new Error('Network response was not ok.');
        }

        const data = await response.json();
        document.getElementById('transcription').textContent = data.transcription;
        document.getElementById('summary').textContent = data.summary;
    } catch (error) {
        console.error('Error:', error);
    }
});
