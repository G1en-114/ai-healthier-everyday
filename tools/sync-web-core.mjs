#!/usr/bin/env node
/**
 * Sync the tested deterministic pose rules from the miniprogram core into the
 * web app as a browser global. Single source of truth: miniprogram/core/poseRules.js
 * (the file covered by `node --test test/*.test.js`).
 *
 * Usage: node tools/sync-web-core.mjs
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const src = join(root, "miniprogram", "core", "poseRules.js");
const dst = join(root, "webapp", "js", "poseRules.js");

const EXPORT_LINE = /module\.exports\s*=\s*\{[^}]+\};?/;
const raw = readFileSync(src, "utf8");
if (!EXPORT_LINE.test(raw)) {
  throw new Error("poseRules.js: module.exports line not found — sync script needs an update");
}

const footer = `if (typeof module !== "undefined" && module.exports) {
  module.exports = { KEYPOINT_INDEX, computeAngles, evaluateRep, RepCounter, EXERCISE_RULES, severityFromDeviation };
} else {
  window.PoseRules = { KEYPOINT_INDEX, computeAngles, evaluateRep, RepCounter, EXERCISE_RULES, severityFromDeviation };
}
`;

const banner = `/*
 * GENERATED FILE — do not edit. Synced from miniprogram/core/poseRules.js by
 * tools/sync-web-core.mjs so the browser and the WeChat miniprogram share the
 * exact same deterministic rep-counting rules (the ones the tests cover).
 */
`;

writeFileSync(dst, banner + raw.replace(EXPORT_LINE, "").trimEnd() + "\n\n" + footer);
console.log(`synced ${src} -> ${dst}`);
