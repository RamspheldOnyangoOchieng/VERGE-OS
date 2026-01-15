// Socket initialization
const socket = io();

// =========================
// THREE.JS SETUP (3D View)
// =========================
const container = document.getElementById('canvas-container');
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });

renderer.setSize(container.clientWidth, container.clientHeight);
container.appendChild(renderer.domElement);

const geometry = new THREE.BoxGeometry(3, 0.5, 5);
const material = new THREE.MeshPhongMaterial({
    color: 0x00ff88,
    shininess: 100,
    transparent: true,
    opacity: 0.8
});
const device = new THREE.Mesh(geometry, material);
scene.add(device);

const wireframe = new THREE.WireframeGeometry(geometry);
const line = new THREE.LineSegments(wireframe);
line.material.color.setHex(0xffffff);
line.material.transparent = true;
line.material.opacity = 0.2;
device.add(line);

const light = new THREE.DirectionalLight(0xffffff, 1);
light.position.set(1, 1, 2).normalize();
scene.add(light);
scene.add(new THREE.AmbientLight(0x404040));

camera.position.z = 8;
camera.position.y = 2;
camera.lookAt(0, 0, 0);

let targetRotX = 0;
let targetRotZ = 0;

function animate() {
    requestAnimationFrame(animate);
    device.rotation.x += (targetRotX - device.rotation.x) * 0.1;
    device.rotation.z += (targetRotZ - device.rotation.z) * 0.1;
    renderer.render(scene, camera);
}
animate();

window.addEventListener('resize', () => {
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
});

// =========================
// LEAFLET MAP SETUP
// =========================
const map = L.map('map').setView([-1.286389, 36.817223], 13);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png').addTo(map);

let marker = L.circleMarker([-1.286389, 36.817223], {
    color: '#00ff88',
    radius: 10
}).addTo(map);

// =========================
// CHART.JS SETUP
// =========================
const ctx = document.getElementById('trendChart').getContext('2d');
const trendChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'X',
            data: [],
            borderColor: '#00ff88',
            tension: 0.4,
            fill: false
        }, {
            label: 'Y',
            data: [],
            borderColor: '#00a35c',
            tension: 0.4,
            fill: false
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        scales: {
            x: { display: true },
            y: { min: -2, max: 2 }
        }
    }
});

// =========================
// THEME SWITCHING
// =========================
const themeToggle = document.getElementById('theme-toggle');
const root = document.documentElement;

themeToggle.addEventListener('click', () => {
    const isLight = root.getAttribute('data-theme') === 'light';
    const newTheme = isLight ? 'dark' : 'light';
    root.setAttribute('data-theme', newTheme);

    // Update colors
    const textColor = newTheme === 'light' ? '#00373d' : '#e0ffe0';
    trendChart.options.scales.x.ticks.color = textColor;
    trendChart.options.scales.y.ticks.color = textColor;
    trendChart.update();

    device.material.color.setHex(newTheme === 'light' ? 0x00bcd4 : 0x00ff88);
});

// =========================
// DATA UPDATES (CLEANED)
// =========================
let processedIds = new Set(); // Stricter duplicate check

socket.on('sensor_data', (data) => {
    // 1. HARD BLOCK DUPLICATES
    if (processedIds.has(data.id) || data.id === -1) return;
    processedIds.add(data.id);

    // Keep set size manageable
    if (processedIds.size > 50) {
        const firstValue = processedIds.values().next().value;
        processedIds.delete(firstValue);
    }

    // 2. Update UI
    document.getElementById('system-mode').innerText = data.mode;
    targetRotX = data.ay * Math.PI / 2;
    targetRotZ = -data.ax * Math.PI / 2;

    trendChart.data.labels.push(data.timestamp);
    trendChart.data.datasets[0].data.push(data.ax);
    trendChart.data.datasets[1].data.push(data.ay);
    if (trendChart.data.labels.length > 10) {
        trendChart.data.labels.shift();
        trendChart.data.datasets[0].data.shift();
        trendChart.data.datasets[1].data.shift();
    }
    trendChart.update('none');

    document.getElementById('val-ax').innerText = data.ax;
    document.getElementById('val-ay').innerText = data.ay;
    document.getElementById('val-gforce').innerText = data.gforce;

    const alertStatus = document.getElementById('alert-status');
    alertStatus.innerText = data.alert ? "STATUS: ALERT" : "STATUS: SECURE";
    alertStatus.style.color = data.alert ? "var(--danger)" : "var(--success)";
});
