// --- КОНСТАНТЫ API ---
const MOON_PHASE_API_URL = 'https://api.farmsense.net/v1/moonphases/?d=';
const API_KEY = 'e9365275dccb4340809289b142ce14ee'; 
const LATITUDE = '43.238949'; 
const LONGITUDE = '76.889709';


// --- BABYLON.JS SETUP ---
const canvas = document.getElementById("renderCanvas");
const engine = new BABYLON.Engine(canvas, true);

const createScene = function () {
    const scene = new BABYLON.Scene(engine);
    scene.clearColor = new BABYLON.Color3(0, 0, 0); // Черный фон

    // Камера
    const camera = new BABYLON.ArcRotateCamera(
        "camera",
        Math.PI / 2,
        Math.PI / 2,
        5,
        BABYLON.Vector3.Zero(),
        scene
    );
    camera.attachControl(canvas, true);
    camera.lowerRadiusLimit = 3;
    camera.upperRadiusLimit = 10;

    // Сфера Луны
    const moon = BABYLON.MeshBuilder.CreateSphere("moon", { diameter: 2, segments: 64 }, scene);

    // Материал Луны
    const moonMaterial = new BABYLON.StandardMaterial("moonMaterial", scene);
    moonMaterial.diffuseTexture = new BABYLON.Texture(
        "https://cdn.jsdelivr.net/gh/mrdoob/three.js@master/examples/textures/planets/moon_1024.jpg",
        scene
    );
    moonMaterial.specularColor = new BABYLON.Color3(0.1, 0.1, 0.1);
    moon.material = moonMaterial;

    // Свет 1: Ambient Light
    const ambientLight = new BABYLON.HemisphericLight(
        "hemiLight",
        new BABYLON.Vector3(0, 1, 0),
        scene
    );
    ambientLight.intensity = 0.1;

    // Свет 2: Солнце
    const sunLight = new BABYLON.DirectionalLight(
        "sunLight",
        new BABYLON.Vector3(1, 0, 0),
        scene
    );
    sunLight.intensity = 0;

    // UI для текста
    const advancedTexture = BABYLON.GUI.AdvancedDynamicTexture.CreateFullscreenUI("UI");

    const phaseText = new BABYLON.GUI.TextBlock();
    phaseText.text = "";
    phaseText.color = "white";
    phaseText.fontSize = 24;
    phaseText.top = "-45%";
    advancedTexture.addControl(phaseText);

    // Добавим "тень" поверх Луны
    const darkOverlay = BABYLON.MeshBuilder.CreateSphere("darkSide", { diameter: 2.01, segments: 64 }, scene);
    const darkMat = new BABYLON.StandardMaterial("darkMat", scene);
    darkMat.diffuseColor = new BABYLON.Color3(0, 0, 0);
    darkMat.alpha = 0.5;
    darkOverlay.material = darkMat;
    darkOverlay.parent = moon;

    // --- ОБНОВЛЕНИЕ ОСВЕЩЕНИЯ ---
    scene.updateMoonIllumination = function (illuminationPercentage, phaseName = "") {
        const intensity = illuminationPercentage / 100;

        // Интенсивность света
        sunLight.intensity = intensity * 1.5;

        // Положение источника света в зависимости от фазы
        const phaseAngle = (illuminationPercentage / 100) * Math.PI;
        const lightX = Math.cos(phaseAngle);
        const lightZ = Math.sin(phaseAngle);
        sunLight.direction = new BABYLON.Vector3(lightX, 0, lightZ);

        // Вращаем Луну
        moon.rotation.y = phaseAngle;

        // Поворачиваем "тень" наоборот
        darkOverlay.rotation.y = phaseAngle + Math.PI;

        console.log(
            `Moon Illumination: ${illuminationPercentage}%. Light Direction: ${sunLight.direction}`
        );
        phaseText.text = `Moon Phase: ${phaseName} (${illuminationPercentage.toFixed(1)}%)`;
    };

    return scene;
};

// Создаём сцену
const scene = createScene();

// --- ФУНКЦИЯ ЗАГРУЗКИ ДАННЫХ API ---
async function fetchMoonData(date = new Date()) {
    // создаём переменную здесь
    const formattedDate = date.toISOString().split("T")[0]; // yyyy-MM-dd
    const apiUrl = `http://localhost:8080/api/moon-phase?date=${formattedDate}`;

    try {
        const response = await fetch(apiUrl);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const moonData = await response.json();
        console.log("Moon data:", moonData);

        const illumination = parseFloat(moonData.Illumination || 100);
        const phaseName = moonData.Phase || "Unknown";

        scene.updateMoonIllumination(illumination, phaseName);
    } catch (error) {
        console.error("Could not fetch moon data:", error);
        scene.updateMoonIllumination(100, "Full Moon");
    }
}






// --- Инициализация Flatpickr ---
flatpickr("#moonDatePicker", {
    dateFormat: "Y-m-d",
    defaultDate: new Date(),
    onChange: function (selectedDates, dateStr, instance) {
        if (selectedDates.length > 0) {
            fetchMoonData(selectedDates[0]);
        }
    },
});

// Запускаем сразу
fetchMoonData(new Date());

// --- RENDER LOOP ---
engine.runRenderLoop(function () {
    scene.render();
});

// --- Обновление при изменении размера окна ---
window.addEventListener("resize", function () {
    engine.resize();
});
