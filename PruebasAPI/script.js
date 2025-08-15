document.getElementById('sendButton').addEventListener('click', async () => {
    const url = document.getElementById('urlInput').value;
    const payloadText = document.getElementById('payloadInput').value;
    const responseDisplay = document.getElementById('responseDisplay');

    responseDisplay.textContent = 'Enviando solicitud...';

    try {
        const payload = JSON.parse(payloadText);

        const response = await fetch(url, {
            method: 'POST', // Puedes cambiar esto a 'GET', 'PUT', 'DELETE', etc.
            headers: {
                'Content-Type': 'application/json',
                // Si tu API requiere algún header adicional (como 'Authorization'), puedes agregarlo aquí.
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        
        // Muestra la respuesta en formato JSON legible
        responseDisplay.textContent = JSON.stringify(data, null, 2);

        if (!response.ok) {
            responseDisplay.textContent = `Error ${response.status}: ${response.statusText}\n` + responseDisplay.textContent;
            responseDisplay.style.color = 'red';
        } else {
            responseDisplay.style.color = 'green';
        }

    } catch (error) {
        responseDisplay.textContent = `Error al procesar la solicitud: ${error.message}`;
        responseDisplay.style.color = 'red';
    }
});