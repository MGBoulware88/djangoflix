function showProfileForm() {
    const addProfileBtn = document.getElementById("addProfileBtn")
    const addProfileForm = document.getElementById("addProfileForm")
    const nameElement = document.getElementById("id_profile_name")
    addProfileBtn.classList.toggle("d-none")
    addProfileForm.classList.toggle("d-none")
    nameElement.focus()

}