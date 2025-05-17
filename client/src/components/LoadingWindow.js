import React from "react";

const LoadingWindow = ({ progress }) => {
    return (
        <div className="loading-window">
            <h2>Обработка видео</h2>
            <p>Ваше видео проходит детекцию. Это займет пару минут.</p>

            <div className="progress-container">
                <div
                    className="progress-bar"
                    style={{ width: `${progress}%` }}
                ></div>
                <span className="progress-text">{Math.round(progress)}%</span>
            </div>

            <p className="status-message">
                {progress < 30 && "Показываем видео, где вход в инференс..."}
                {progress >= 30 &&
                    progress < 70 &&
                    "Модель крутит ваше видео во всех ракурсах..."}
                {progress >= 70 &&
                    progress < 100 &&
                    "Модель формирует выводы..."}
                {progress === 100 && "Обработка выполнена!"}
            </p>
        </div>
    );
};

export default LoadingWindow;
