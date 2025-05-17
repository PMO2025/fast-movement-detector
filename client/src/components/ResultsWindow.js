import React from "react";

const ResultsWindow = ({ videoUrl, onDownload, onReset }) => {
    return (
        <div className="results-window">
            <h2>Ознакомьтесь с результатом</h2>

            <div className="video-container">
                <video controls src={videoUrl} />
            </div>

            <div className="button-group">
                <button onClick={onReset} className="secondary-button">
                    Загрузить новое видео
                </button>
                <button onClick={onDownload} className="primary-button">
                    Скачать видео
                </button>
            </div>
        </div>
    );
};

export default ResultsWindow;
