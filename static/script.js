document.addEventListener("DOMContentLoaded", function() {
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('fileInput');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const result = document.getElementById('result');
    
    const fileModeButton = document.getElementById('fileMode');
    const pasteModeButton = document.getElementById('pasteMode');
    const faqButton = document.getElementById('faqButton'); // Added FAQ button

    const fileSharingSection = document.getElementById('fileSharingSection');
    const pastebinSection = document.getElementById('pastebinSection');
    const faqSection = document.getElementById('faqSection'); // FAQ section

    const pasteContent = document.getElementById('pasteContent');
    const submitPasteButton = document.getElementById('submitPaste');
    const pasteResult = document.getElementById('pasteResult');
    
    let filesToUpload = [];

    // Toggle between file sharing, pastebin, and FAQ sections
    fileModeButton.addEventListener('click', () => {
        showSection(fileSharingSection);
        hideSection(pastebinSection);
        hideSection(faqSection);
        activateButton(fileModeButton);
    });

    pasteModeButton.addEventListener('click', () => {
        showSection(pastebinSection);
        hideSection(fileSharingSection);
        hideSection(faqSection);
        activateButton(pasteModeButton);
    });

    faqButton.addEventListener('click', () => {
        showSection(faqSection);
        hideSection(fileSharingSection);
        hideSection(pastebinSection);
        activateButton(faqButton);
    });

    // Helper function to show a section
    function showSection(section) {
        section.style.display = 'block';
    }

    // Helper function to hide a section
    function hideSection(section) {
        section.style.display = 'none';
    }

    // Helper function to activate a button
    function activateButton(button) {
        const buttons = [fileModeButton, pasteModeButton, faqButton];
        buttons.forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
    }

    // Make drop area clickable and open file input dialog
    dropArea.addEventListener('click', () => {
        fileInput.click();
    });

    // Drag-and-drop events
    dropArea.addEventListener('dragover', (event) => {
        event.preventDefault();
        dropArea.classList.add('dragging');
    });

    dropArea.addEventListener('dragleave', () => {
        dropArea.classList.remove('dragging');
    });

    dropArea.addEventListener('drop', (event) => {
        event.preventDefault();
        dropArea.classList.remove('dragging');
        
        filesToUpload = event.dataTransfer.files;
        displaySelectedFiles(filesToUpload);
        handleFileUpload(filesToUpload);  // Automatically upload files on drop
    });

    // Handle file input selection
    fileInput.addEventListener('change', (event) => {
        filesToUpload = event.target.files;
        displaySelectedFiles(filesToUpload);
        handleFileUpload(filesToUpload);  // Automatically upload files on selection
    });

    // Helper function to display selected files (with previews for images)
    function displaySelectedFiles(files) {
        result.innerHTML = '<p>Selected Files:</p>';
        
        Array.from(files).forEach(file => {
            const fileElement = document.createElement('div');
            fileElement.classList.add('uploaded-file');
            
            const fileName = document.createElement('p');
            fileName.textContent = file.name;
            fileElement.appendChild(fileName);

            // Generate preview if it's an image
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    img.classList.add('thumbnail-small');
                    fileElement.appendChild(img);
                };
                reader.readAsDataURL(file);
            }

            result.appendChild(fileElement);
        });
    }

    // Handle file upload
    function handleFileUpload(files) {
        const formData = new FormData();

        for (let i = 0; i < files.length; i++) {
            formData.append('files[]', files[i]);
        }

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/upload', true);  // Updated to use /api/upload

        // Handle progress events
        xhr.upload.addEventListener('progress', (event) => {
            if (event.lengthComputable) {
                let percentComplete = Math.round((event.loaded / event.total) * 100);
                progressBar.style.width = percentComplete + '%';
                progressText.textContent = percentComplete + '%';
            }
        });

        // Handle the response from the server
        xhr.onload = function() {
            if (xhr.status === 201) {  // Changed to handle 201 Created response
                const response = JSON.parse(xhr.responseText);
                displayUploadedFiles(response.urls, files);
                progressContainer.style.display = 'none';  // Hide progress bar when done
            } else {
                result.innerHTML = '<p class="error">Error: File upload failed</p>';
                progressContainer.style.display = 'none';
            }
        };

        // Handle network or server errors
        xhr.onerror = function() {
            result.innerHTML = '<p class="error">Error: An error occurred during the upload</p>';
        };

        // Display the progress bar
        progressContainer.style.display = 'block';

        // Send the files
        xhr.send(formData);
    }

    // Display the uploaded file URLs along with previews for image files
    function displayUploadedFiles(urls, files) {
        result.innerHTML = '<p>Uploaded Files:</p>';
        
        urls.forEach((url, index) => {
            const file = files[index];
            const fileElement = document.createElement('div');
            fileElement.classList.add('uploaded-file');
            
            const fileLink = document.createElement('a');
            fileLink.href = url;
            fileLink.target = '_blank';
            fileLink.textContent = file.name;

            fileElement.appendChild(fileLink);

            // Check if the file is an image and add a preview
            if (file.type.startsWith('image/')) {
                const imgPreview = document.createElement('img');
                imgPreview.classList.add('thumbnail-small');
                
                const reader = new FileReader();
                reader.onload = function(e) {
                    imgPreview.src = e.target.result;
                    fileElement.appendChild(imgPreview);
                };
                reader.readAsDataURL(file);
            }

            result.appendChild(fileElement);
        });
    }

    // Handle paste submission
    submitPasteButton.addEventListener('click', () => {
        const pasteData = pasteContent.value;

        if (pasteData.trim() === '') {
            pasteResult.innerHTML = '<p class="error">Error: Paste content cannot be empty</p>';
            return;
        }

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/paste', true);  // Updated to use /api/paste
        xhr.setRequestHeader('Content-Type', 'application/json');

        xhr.onload = function() {
            if (xhr.status === 201) {  // Handle 201 Created response for paste
                const response = JSON.parse(xhr.responseText);
                pasteResult.innerHTML = `<p>Paste URL: <a href="${response.url}" target="_blank">${response.url}</a></p>`;
            } else {
                pasteResult.innerHTML = '<p class="error">Error: Could not save paste</p>';
            }
        };

        xhr.onerror = function() {
            pasteResult.innerHTML = '<p class="error">Error: An error occurred while submitting the paste</p>';
        };

        // Send the paste data
        xhr.send(JSON.stringify({ content: pasteData }));
    });
});
