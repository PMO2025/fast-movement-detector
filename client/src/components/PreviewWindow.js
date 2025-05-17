import React from "react";

const PreviewWindow = ({ videoUrl, onInfer, onBack }) => {
    return (
        <div className="preview-window">
            <h2>Предпросмотр вашего видео</h2>

            <div className="video-container">
                <video controls src={videoUrl} />
            </div>

            <div className="button-group">
                <button onClick={onBack} className="secondary-button">
                    Назад
                </button>
                <button onClick={onInfer} className="primary-button">
                    Отправить
                </button>
            </div>
        </div>
    );
};

export default PreviewWindow;
