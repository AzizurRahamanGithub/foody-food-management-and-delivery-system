// js/multifile_fix.js

document.addEventListener('DOMContentLoaded', function () {
    // Get all file inputs that allow multiple files
    const multiFileInputs = document.querySelectorAll('input[type="file"][multiple]');

    multiFileInputs.forEach(input => {
        let fileList = []; // store all selected files

        input.addEventListener('change', function (e) {
            const newFiles = Array.from(e.target.files);

            // append new files to fileList
            fileList = fileList.concat(newFiles);

            // create a DataTransfer object to update input.files
            const dataTransfer = new DataTransfer();
            fileList.forEach(file => dataTransfer.items.add(file));

            input.files = dataTransfer.files;

            // Optional: show preview or file names
            const previewId = input.getAttribute('id') + '_preview';
            let previewDiv = document.getElementById(previewId);
            if (!previewDiv) {
                previewDiv = document.createElement('div');
                previewDiv.id = previewId;
                previewDiv.style.marginTop = '5px';
                input.parentNode.appendChild(previewDiv);
            }
            previewDiv.innerHTML = '';
            fileList.forEach(file => {
                const p = document.createElement('p');
                p.textContent = file.name;
                previewDiv.appendChild(p);
            });
        });
    });
});


