async function updateEmotion() {
  try {
    const res = await fetch("http://localhost:5000/emotion");
    const data = await res.json();
    document.getElementById("emotion").innerText = data.emotion;
  } catch (err) {
    console.error("Error:", err);
  }
}

setInterval(updateEmotion, 1000); // update every second