// Elemente
const videoElement = document.getElementById('videoInput');
const modelSelector = document.getElementById('modelSelector');

// Three.js Setup
let scene, camera, renderer;
let fingernailModel;
const fingernailMeshes = [];
let videoTexture;

initThreeJS();
setupVideoTexture();
loadFingernailModel(modelSelector.value); // Initiales Laden des ersten Modells

// Event Listener für das Auswahlmenü
modelSelector.addEventListener('change', function () {
  loadFingernailModel(this.value);
});

// Three.js Szene initialisieren
function initThreeJS() {
  scene = new THREE.Scene();

  const width = 640;
  const height = 480;
  camera = new THREE.OrthographicCamera(-width / 2, width / 2, height / 2, -height / 2, 0.1, 2000);

  renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('canvasOutput'), alpha: true });
  renderer.setSize(width, height);
  renderer.setClearColor(0x000000, 0);

  // Beleuchtung hinzufügen
  const ambientLight = new THREE.AmbientLight(0xffffff, 1);
  scene.add(ambientLight);
}

// Video-Textur einrichten
function setupVideoTexture() {
  videoTexture = new THREE.VideoTexture(videoElement);
  videoTexture.minFilter = THREE.LinearFilter;
  videoTexture.magFilter = THREE.LinearFilter;
  videoTexture.format = THREE.RGBFormat;

  const geometry = new THREE.PlaneGeometry(640, 480);
  const material = new THREE.MeshBasicMaterial({ map: videoTexture });
  const plane = new THREE.Mesh(geometry, material);

  plane.position.z = -1000; // Ebene weit nach hinten verschieben
  scene.add(plane);
}

// GLB-Modell laden
function loadFingernailModel(modelPath) {
  // Vorherige Fingernagel-Meshes entfernen
  fingernailMeshes.forEach(mesh => {
    scene.remove(mesh);
  });
  fingernailMeshes.length = 0; // Array leeren

  const loader = new THREE.GLTFLoader();
  loader.load(modelPath, function (gltf) {
    fingernailModel = gltf.scene;

    // Materialien überschreiben (falls notwendig)
    fingernailModel.traverse((node) => {
      if (node.isMesh) {
        node.geometry.center(); // Zentriert die Geometrie
        // Optional: Materialien anpassen
        // node.material = new THREE.MeshBasicMaterial({ color: 0xff00ff });
      }
    });

    // Für jeden Fingernagel ein Klon des Modells erstellen
    for (let i = 0; i < 5; i++) {
      const mesh = fingernailModel.clone();

      // Initiale Rotation hinzufügen
      mesh.rotation.set(0, 0, 0);

      mesh.scale.set(9, 9, 9); // Größe anpassen
      scene.add(mesh);
      fingernailMeshes.push(mesh);
    }

    // Wenn die Animation noch nicht läuft, starten wir sie
    if (!animationStarted) {
      animate();
      animationStarted = true;
    }
  }, undefined, function (error) {
    console.error('Fehler beim Laden des Modells:', error);
  });
}

// Variable, um zu überprüfen, ob die Animation bereits gestartet wurde
let animationStarted = false;

// MediaPipe Hands Setup
const hands = new Hands({
  locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`,
});

hands.setOptions({
  maxNumHands: 1,
  modelComplexity: 1,
  minDetectionConfidence: 0.5,
  minTrackingConfidence: 0.5,
});

hands.onResults(onResults);

const cameraUtils = new Camera(videoElement, {
  onFrame: async () => {
    await hands.send({ image: videoElement });
  },
  width: 640,
  height: 480,
});
cameraUtils.start();

// Variable zur Speicherung der Handlandmarken
let currentLandmarks = null;

// Ergebnisse von MediaPipe Hands verarbeiten
function onResults(results) {
  if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
    currentLandmarks = results.multiHandLandmarks[0];
  } else {
    currentLandmarks = null;
  }
}

// Funktion zur Berechnung des Skalierungsfaktors basierend auf z
function computeScaleFromZ(z) {
  const zAbs = Math.abs(z);

  // Definiere minimale und maximale Skalierungsfaktoren
  const minScale = 0.9;
  const maxScale = 9;

  // Definiere den Bereich der z-Werte, z.B. z zwischen 0 und 0.5
  const zMin = 0;   // Hand sehr nah an der Kamera
  const zMax = 0.5; // Hand weiter von der Kamera entfernt

  // Normalisiere den z-Wert auf den Bereich [0, 1]
  let normalizedZ = (zAbs - zMin) / (zMax - zMin);
  normalizedZ = Math.min(Math.max(normalizedZ, 0), 1); // Begrenzung auf [0, 1]

  // Invertiere den Wert, damit bei kleinerem z der Skalierungsfaktor größer wird
  const scale = minScale + (normalizedZ * (maxScale - minScale));

  return scale;
}

// Animationsschleife
function animate() {
  requestAnimationFrame(animate);

  if (currentLandmarks && fingernailMeshes.length === 5) {
    const landmarks = currentLandmarks;
    const fingertipIndices = [4, 8, 12, 16, 20];

    for (let i = 0; i < fingertipIndices.length; i++) {
      const tipIndex = fingertipIndices[i];
      const jointIndex = tipIndex - 1;

      const tipLandmark = landmarks[tipIndex];
      const jointLandmark = landmarks[jointIndex];

      const canvasWidth = 640;
      const canvasHeight = 480;

      // Koordinatentransformation
      const xMP = tipLandmark.x * canvasWidth;
      const yMP = tipLandmark.y * canvasHeight;

      const x = xMP - (canvasWidth / 2);
      const y = (canvasHeight / 2) - yMP;

      const mesh = fingernailMeshes[i];
      mesh.position.set(x, y, -50); // Z-Position bei Bedarf anpassen

      // Winkelberechnung
      const dx = jointLandmark.x - tipLandmark.x;
      const dy = jointLandmark.y - tipLandmark.y;x
      const angle = Math.atan2(dy, dx);

      // Rotation des Meshes setzen
      const rotationOffset = 4.8; // Anpassen nach Bedarf
      mesh.rotation.z = -angle + rotationOffset;

      // **Dynamische Skalierung basierend auf der Tiefe**
      const z = tipLandmark.z;
      const scale = computeScaleFromZ(z);
      mesh.scale.set(scale, scale, scale);
    }
  }

  renderer.render(scene, camera);
}