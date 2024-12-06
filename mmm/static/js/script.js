// button to close message box
function closeMessageBox(id) {
    var messageBox = document.getElementById(id);
    messageBox.style.display = "none";
}

// button to affirm deletion
function confirmDelete() {
    return confirm('Are you sure you want to delete this project/file? (cannot be undone)');
}

/**
 * Highlights files based on their extensions.
 * @param {Array} extension_list - The list of file extensions to highlight.
 */
function highlightFiles(extension_list) {
    var files = document.getElementsByClassName("phimisci-mmm-file-selection");
    for (var i = 0; i < files.length; i++) {
        var file = files[i].textContent.trim();
        // split filename to get extension
        if (file.includes(".")) {
            var file_extension = file.split('.').pop();
        } else {
            var file_extension = "";
        }
        if (extension_list.includes(file_extension)) {
            // highlight file in orange
            files[i].style.backgroundColor = "#eb6b06";
        } else {
            files[i].style.backgroundColor = "#ffffff";
        }
    }
}

/**
 * Starts the loading animation and submits the form if it is valid.
 */
function startLoadingAnimation() {
    // remove submit button
    var submitButton = document.getElementById("submit-phimisci");
    // get form element
    var form = document.getElementById("phimisci-form-field");
    // only submit form and start loading animation if it is valid
    if (form.checkValidity()) {
        submitButton.style.display = "none";
        // get loading element container
        var loadingContainer = document.getElementById("loading-container-phimisci");
        loadingContainer.style.display = "block";
        // get loading element
        var loadingBlock = document.getElementById("loading-animation-phimisci");
        loadingBlock.style.display = "block";
    }
}