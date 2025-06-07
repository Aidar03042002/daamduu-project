document.getElementById("login-form").addEventListener("submit", async function (e) {
    e.preventDefault();

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    const response = await fetch("http://localhost:8080/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
            username: username,
            password: password,
        }),
    });

    if (response.ok) {
        // Başarılı giriş
        window.location.href = "/ana-sayfa.html";
    } else {
        // Hatalı giriş
        document.getElementById("error-msg").innerText = "Kullanıcı adı veya şifre yanlış";
    }
});
