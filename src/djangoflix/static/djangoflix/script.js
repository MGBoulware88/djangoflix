function toggleProfileForm(focus) {
    const addProfileBtn = document.getElementById("addProfileBtn");
    const addProfileFormDiv = document.getElementById("addProfileFormDiv");
    addProfileBtn.classList.toggle("d-none");
    addProfileFormDiv.classList.toggle("d-none");
    
    if (focus) {
        const nameElement = document.getElementById("id_profile_name");
        nameElement.focus();
    }
}


function submitForm() {
    const profileForm = document.getElementById("addProfileForm")
    profileForm.submit()
}