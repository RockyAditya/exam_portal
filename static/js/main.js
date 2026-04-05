document.addEventListener('DOMContentLoaded', () => {
    // Auto-dismiss toasts
    setTimeout(() => {
        const toasts = document.querySelectorAll('.toast');
        toasts.forEach(t => t.remove());
    }, 5000);

    // File Upload styling and interaction
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        const uploadZone = input.closest('.upload-zone');
        if (uploadZone) {
            uploadZone.addEventListener('click', () => input.click());

            uploadZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadZone.classList.add('dragover');
            });

            uploadZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                uploadZone.classList.remove('dragover');
            });

            uploadZone.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadZone.classList.remove('dragover');
                if (e.dataTransfer.files.length) {
                    input.files = e.dataTransfer.files;
                    updateFileName(input, uploadZone);
                }
            });

            input.addEventListener('change', () => {
                updateFileName(input, uploadZone);
            });
        }
    });

    function updateFileName(input, zone) {
        if(input.files.length > 0) {
            const fileName = input.files[0].name;
            let textElem = zone.querySelector('p');
            if(!textElem) {
                textElem = document.createElement('p');
                zone.appendChild(textElem);
            }
            textElem.innerHTML = `<i class="fas fa-file"></i> Selected: ${fileName}`;
        }
    }
});
