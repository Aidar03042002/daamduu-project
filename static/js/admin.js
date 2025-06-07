document.addEventListener("DOMContentLoaded", () => {
  // === MENU ===
  const menuForm = document.querySelector("form");
  const menuTable = document.getElementById("menu-table");

  if (menuForm && menuTable) {
    menuForm.addEventListener("submit", function (e) {
      e.preventDefault();
      const nameInput = document.getElementById("menu-item");
      const calorieInput = document.getElementById("calorie");
      const imageInput = document.getElementById("food-image");
      const dateInput = document.getElementById("menu-date");

      const name = nameInput.value.trim();
      const calorie = calorieInput.value.trim();
      const imageFile = imageInput.files[0];
      const selectedDate = dateInput.value;

      if (!name || !calorie || !imageFile) return;

      // Tarih formatı belirle
      let formattedDate = "";
      let dayStr = "";

      if (selectedDate) {
        const date = new Date(selectedDate);
        formattedDate = date.toLocaleDateString("tr-TR");
        dayStr = date.toLocaleDateString("tr-TR", { weekday: 'long' });
      } else {
        const now = new Date();
        formattedDate = now.toLocaleDateString("tr-TR");
        dayStr = now.toLocaleDateString("tr-TR", { weekday: 'long' });
      }

      const reader = new FileReader();
      reader.onload = function (e) {
        const newRow = document.createElement("tr");
        newRow.innerHTML = `
        <td><strong>${name}</strong></td>
        <td><strong>${calorie}</strong></td>
        <td><img src="${e.target.result}" alt="yemek" style="width: 60px; height: 60px; object-fit: cover; border-radius: 8px;"></td>
        <td><strong>${formattedDate} (${dayStr})</strong></td>
        <td><button class="btn btn-danger btn-sm delete-btn">Sil</button></td>
`;


        menuTable.appendChild(newRow);
        nameInput.value = "";
        calorieInput.value = "";
        imageInput.value = "";
        dateInput.value = "";
      };
      reader.readAsDataURL(imageFile);
    });

    menuTable.addEventListener("click", function (e) {
      if (e.target.classList.contains("delete-btn")) {
        e.target.closest("tr").remove();
      }
    });
  }

  // === şifremi unuttum ===
  function sendResetEmail() {
    const email = document.getElementById("reset-email").value;
    const successMsg = document.getElementById("reset-success");
  
    if (email.includes("@")) {
      successMsg.classList.remove("d-none");
      setTimeout(() => {
        successMsg.classList.add("d-none");
        const modal = bootstrap.Modal.getInstance(document.getElementById('forgotPasswordModal'));
        modal.hide();
      }, 2000);
    } else {
      alert("Lütfen geçerli bir e-posta adresi girin.");
    }
  }
  

  // === USERS ===
  const userTable = document.querySelector("table");
  if (userTable) {
    userTable.addEventListener("click", function (e) {
      const row = e.target.closest("tr");
      const cells = row.querySelectorAll("td");

      if (e.target.textContent === "Sıfırla") {
        if (cells[3]) cells[3].textContent = "0";
      } else if (e.target.textContent === "Sil") {
        row.remove();
      }
    });
  }
});
