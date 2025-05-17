// Нужна ссылка на API.
const API_BASE_URL = "http://localhost:8000";

export const uploadVideo = async (file) => {
    const formData = new FormData();
    formData.append("video", file);

    const response = await fetch(`${API_BASE_URL}/upload`, {
        method: "POST",
        body: formData,
    });

    if (!response.ok) {
        throw new Error("Upload failed");
    }

    return response.json();
};

export const checkStatus = (id, onMessage) => {
    const eventSource = new EventSource(`${API_BASE_URL}/status?id=${id}`);

    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        onMessage(data);

        if (
            data.status === "completed" ||
            data.status === "failed" ||
            data.status === "error"
        ) {
            eventSource.close();
        }
    };

    eventSource.onerror = () => {
        eventSource.close();
        onMessage({ status: "error", error: "Connection failed" });
    };

    return eventSource;
};

export const getVideoURL = (id) => {
    return `${API_BASE_URL}/download?id=${id}`;
};

export const downloadVideo = async (id) => {
    const response = await fetch(getVideoURL(id));

    if (!response.ok) {
        throw new Error("Download failed");
    }

    console.log(response);

    return response.blob();
};
