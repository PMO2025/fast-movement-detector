<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://github.com/PMO2025/fast-movement-detector">
    <img src="./docs_src/run-from-me-preview.jpg" alt="Logo" width="150" height="150">
  </a>

  <h3 align="center">Детектор резкого ускорения в кадре</h3>
</p>

<p align="center">
  <a href="https://github.com/egormalyutin/"><b>Егор Малютин</b></a> · <a href="https://github.com/ribus2005/"><b>Лев Морякин</b></a> · <a href="https://github.com/703lovelost/"><b>Алексей Спиркин</b></a>
  <br />
  Институт Интеллектуальной Робототехники
  <br />
  Под кураторством м.н.с. ЦИИ НГУ В.Ю. Кудинова
</p>

<p align="center">
  В данной работе представлен детектор резкого ускорения объектов в видеопотоке
  <br />
  <a href="#">Ознакомиться с демо</a>
  ·
  <a href="https://github.com/PMO2025/fast-movement-detector/issues">Описать баг</a>
  ·
  <a href="https://github.com/PMO2025/fast-movement-detector/issues">Предложить доработку</a>
</p>

<!-- TABLE OF CONTENTS -->
<details open="open">
  <summary>Содержание</summary>
  <ol>
    <li><a href="#О-проекте">О проекте</a></li>
    <li><a href="#Как-использовать-детектор">Подготовка</a></li>
    <li><a href="#Инференс-видео">Инференс видео</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## О проекте

Вся детальная информация о проекте и путях его назначения представлена в [документе системного дизайна проекта](SystemDesign.md).

<!-- PREPARATION -->
## Подготовка

Выгрузите материалы для инференса в папку `videos`.

<!-- USAGE EXAMPLES -->
## Инференс видео

В данный момент инференс производится только по одному видеоролику, цикл обработки всего набора видео не предусмотрен.

Укажите путь к видеоролику в переменной `source_path`.
