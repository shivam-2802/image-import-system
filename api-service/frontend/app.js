async function importImages() {
  const input = document.getElementById("folderUrl");
  const folderUrl = input.value.trim();

  if (!folderUrl) {
    alert("Please enter a folder URL");
    return;
  }

  await fetch("/import/google-drive", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ folder_url: folderUrl })
  });

  alert("Import started");
  input.value = "";
}

async function loadImages() {
  const response = await fetch("/images");
  const images = await response.json();

  const gallery = document.getElementById("gallery");
  gallery.innerHTML = "";

  images.forEach(img => {
    const imageEl = document.createElement("img");
    imageEl.src = img.url;
    imageEl.alt = img.name;
    gallery.appendChild(imageEl);
  });
}


loadImages();
