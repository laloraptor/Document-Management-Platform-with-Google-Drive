function toggleForms() {
    var searchForms = document.getElementById("search-forms");
    var uploadForm = document.getElementById("upload-form");
    if (searchForms.style.display === "none" || searchForms.style.display === "") {
        searchForms.style.display = "block";
        uploadForm.style.display = "none";
    } else {
        searchForms.style.display = "none";
        uploadForm.style.display = "none";
    }
}

function toggleUploadForm() {
    var uploadForm = document.getElementById("upload-form");
    var searchForms = document.getElementById("search-forms");
    if (uploadForm.style.display === "none" || uploadForm.style.display === "") {
        uploadForm.style.display = "block";
        searchForms.style.display = "none";
    } else {
        uploadForm.style.display = "none";
        searchForms.style.display = "none";
    }
}

function toggleNewCategoryField() {
    var labelDropdown = document.getElementById("label");
    var newLabelLabel = document.getElementById("newLabelLabel");
    var newLabelInput = document.getElementById("new_label");
    if (labelDropdown.value === "nueva_categoria") {
        newLabelLabel.style.display = "block";
        newLabelInput.style.display = "block";
    } else {
        newLabelLabel.style.display = "none";
        newLabelInput.style.display = "none";
    }
}

function showProgressBar() {
    document.getElementById("progress-bar").style.display = "block";
}

function hideProgressBar() {
    document.getElementById("progress-bar").style.display = "none";
}

function checkFileStatus(fileId) {
    // Realiza una solicitud para verificar el estado del archivo en Google Drive
    fetch(`/check_file_status/${fileId}`)
        .then(response => response.json())
        .then(data => {
            if (data.exists) {
                // Si el archivo existe, recarga la página
                location.reload();
            } else {
                // Si el archivo no existe, sigue comprobando después de 1 segundo
                setTimeout(() => {
                    checkFileStatus(fileId);
                }, 1000);
            }
        })
        .catch(error => {
            console.error('Error al verificar el estado del archivo:', error);
        });
}

function handleUploadSuccess(fileId) {
    // Esta función se llama después de que se sube el archivo con éxito
    // Puedes realizar las acciones necesarias aquí antes de verificar la carpeta

    // Por ejemplo, mostrar un mensaje de éxito o realizar otras acciones necesarias
    document.getElementById("progress-bar").style.display = "block";
    document.getElementById("upload-success").style.display = "block";
    document.getElementById("upload-success").setAttribute("data-file-id", fileId);

    // Espera 1 segundo antes de verificar la existencia de la carpeta
    setTimeout(() => {
        checkFolderStatus(fileId);
    }, 1000);
}

// Función para convertir la consulta de búsqueda a mayúsculas
function toUpperCase() {
    var searchInput = document.getElementById("search_label");
    searchInput.value = searchInput.value.toUpperCase();
}

function convertToUpperCase() {
    var searchInput = document.getElementById("search_label");
    searchInput.value = searchInput.value.toUpperCase();
}
