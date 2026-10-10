/* In-browser pose AI: MediaPipe Pose Landmarker (CDN) + the project's
 * deterministic rep-counting rules (window.PoseRules, synced from the
 * miniprogram core). Video frames never leave the device — only landmark
 * math happens here, entirely client-side.
 */
(function () {
  const MP_SCRIPT = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/vision_bundle.mjs";
  const MP_WASM = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm";
  const MP_MODEL =
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task";

  // BlazePose-33 → the project's body-18 layout (only 0..13 used).
  // Angles are dot-product based, so normalized coordinates are fine.
  const MAP = {
    nose: 0, r_shoulder: 12, r_elbow: 14, r_wrist: 16,
    l_shoulder: 11, l_elbow: 13, l_wrist: 15,
    r_hip: 24, r_knee: 26, r_ankle: 28, l_hip: 23, l_knee: 25, l_ankle: 27,
  };
  const CONF_SLOTS = [12, 14, 16, 11, 13, 15, 24, 26, 28, 23, 25, 27]; // order of body-18 2..13
  const SKELETON = [
    [11, 12], [11, 23], [12, 24], [23, 24],
    [11, 13], [13, 15], [12, 14], [14, 16],
    [23, 25], [25, 27], [24, 26], [26, 28],
  ];

  let landmarker = undefined; // undefined = not loaded, false = failed, object = ready

  async function ensureModel() {
    if (landmarker !== undefined) return landmarker;
    try {
      const vision = await import(/* @vite-ignore */ MP_SCRIPT);
      const files = await vision.FilesetResolver.forVisionTasks(MP_WASM);
      landmarker = await vision.PoseLandmarker.createFromOptions(files, {
        baseOptions: { modelAssetPath: MP_MODEL, delegate: "GPU" },
        runningMode: "VIDEO",
        numPoses: 1,
      });
    } catch (err) {
      console.warn("pose model unavailable:", err);
      landmarker = false;
    }
    return landmarker;
  }

  function toBody18(lms) {
    const pts = new Array(18).fill(null);
    const conf = new Array(18).fill(1);
    const get = (i) => ({ x: lms[i].x, y: lms[i].y });
    for (const [name, idx] of Object.entries(MAP)) pts[window.PoseRules.KEYPOINT_INDEX[name]] = get(idx);
    // neck = midpoint of shoulders
    const K = window.PoseRules.KEYPOINT_INDEX;
    pts[K.neck] = {
      x: (lms[MAP.l_shoulder].x + lms[MAP.r_shoulder].x) / 2,
      y: (lms[MAP.l_shoulder].y + lms[MAP.r_shoulder].y) / 2,
    };
    conf[K.neck] = Math.min(lms[MAP.l_shoulder].visibility, lms[MAP.r_shoulder].visibility);
    CONF_SLOTS.forEach((mpIdx, i) => {
      conf[2 + i] = lms[mpIdx].visibility; // body-18 slots 2..13, same order as CONF_SLOTS
    });
    return { pts, conf };
  }

  function drawSkeleton(ctx, lms, w, h) {
    ctx.clearRect(0, 0, w, h);
    ctx.lineWidth = Math.max(2, w / 320);
    ctx.strokeStyle = "rgba(94, 234, 212, 0.9)";
    ctx.beginPath();
    for (const [a, b] of SKELETON) {
      const pa = lms[a], pb = lms[b];
      if (!pa || !pb || pa.visibility < 0.4 || pb.visibility < 0.4) continue;
      ctx.moveTo(pa.x * w, pa.y * h);
      ctx.lineTo(pb.x * w, pb.y * h);
    }
    ctx.stroke();
    ctx.fillStyle = "rgba(45, 212, 191, 0.95)";
    for (const lm of lms) {
      if (lm.visibility < 0.4) continue;
      ctx.beginPath();
      ctx.arc(lm.x * w, lm.y * h, Math.max(3, w / 220), 0, Math.PI * 2);
      ctx.fill();
    }
  }

  /**
   * Run a camera session.
   * @param {Object} opts {video, canvas, exerciseKey, counters: {onRep, onPartial, onCue}}
   * @returns {Promise<{ok:boolean, reason?:string}>}
   */
  async function start(opts) {
    const model = await ensureModel();
    if (!model) return { ok: false, reason: "model" };
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 960 }, height: { ideal: 720 } },
        audio: false,
      });
    } catch (err) {
      return { ok: false, reason: "camera" };
    }
    const video = opts.video;
    video.srcObject = stream;
    await video.play();

    const canvas = opts.canvas;
    const ctx = canvas.getContext("2d");
    const counter = new window.PoseRules.RepCounter(opts.exerciseKey);
    let running = true;
    let lastTs = -1;
    let lowConfFrames = 0;

    function loop() {
      if (!running) return;
      if (video.readyState >= 2 && video.currentTime !== lastTs) {
        lastTs = video.currentTime;
        const w = canvas.width = video.videoWidth || 960;
        const h = canvas.height = video.videoHeight || 720;
        try {
          const res = model.detectForVideo(video, performance.now());
          const lms = res && res.landmarks && res.landmarks[0];
          if (lms && lms.length >= 29) {
            drawSkeleton(ctx, lms, w, h);
            const { pts, conf } = toBody18(lms);
            const frame = window.PoseRules.computeAngles(pts, conf);
            const out = counter.update(frame);
            if (frame.meanConfidence < 0.5) {
              lowConfFrames++;
              if (lowConfFrames % 15 === 1) opts.counters.onCue({ lowConf: true });
            } else {
              lowConfFrames = 0;
              if (out.hint === null && out.analysis === null) opts.counters.onCue({ phase: counter.state });
            }
            if (out.repCompleted && out.analysis) opts.counters.onRep(out.analysis);
            else if (out.partial && out.analysis) opts.counters.onPartial(out.analysis);
            else if (out.repCompleted) opts.counters.onRep(null);
          } else {
            ctx.clearRect(0, 0, w, h);
            opts.counters.onCue({ lowConf: true });
          }
        } catch (err) {
          console.warn("frame error", err);
        }
      }
      requestAnimationFrame(loop);
    }
    requestAnimationFrame(loop);

    return {
      ok: true,
      async stop() {
        running = false;
        const tail = counter.finishDip();
        if (tail && tail.repCompleted && tail.analysis) opts.counters.onRep(tail.analysis);
        stream.getTracks().forEach((tr) => tr.stop());
        video.srcObject = null;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      },
    };
  }

  window.PoseCam = { ensureModel, start };
})();
