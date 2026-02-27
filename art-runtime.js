(function (global) {
  'use strict';

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function frameLerp(current, target, alphaPerFrame, frameDelta) {
    const alpha = clamp(alphaPerFrame, 0, 1);
    const d = Math.max(0, frameDelta || 0);
    const blended = 1 - Math.pow(1 - alpha, d);
    return current + (target - current) * blended;
  }

  function frameDecay(value, decayPerFrame, frameDelta) {
    const decay = clamp(decayPerFrame, 0, 1);
    const d = Math.max(0, frameDelta || 0);
    return value * Math.pow(decay, d);
  }

  function frameChance(probPerFrame, frameDelta) {
    const p = clamp(probPerFrame, 0, 1);
    const d = Math.max(0, frameDelta || 0);
    const chance = 1 - Math.pow(1 - p, d);
    return Math.random() < chance;
  }

  function createClock(options) {
    const config = Object.assign({
      baselineFps: 60,
      minDtSec: 1 / 240,
      maxDtSec: 0.05,
      timeScale: 1
    }, options || {});

    let lastNowSec = null;
    let elapsedSec = 0;

    return {
      tick(nowMs) {
        const nowSec = (typeof nowMs === 'number' ? nowMs : performance.now()) / 1000;

        if (lastNowSec === null) {
          lastNowSec = nowSec;
          const dtSec = clamp(1 / config.baselineFps, config.minDtSec, config.maxDtSec) * config.timeScale;
          elapsedSec += dtSec;
          return {
            dtSec,
            frameDelta: dtSec * config.baselineFps,
            elapsedSec
          };
        }

        const rawDtSec = nowSec - lastNowSec;
        lastNowSec = nowSec;

        const dtSec = clamp(rawDtSec, config.minDtSec, config.maxDtSec) * config.timeScale;
        elapsedSec += dtSec;

        return {
          dtSec,
          frameDelta: dtSec * config.baselineFps,
          elapsedSec
        };
      },
      reset() {
        lastNowSec = null;
        elapsedSec = 0;
      }
    };
  }

  global.PhosphorRuntime = {
    createClock,
    frameLerp,
    frameDecay,
    frameChance
  };
})(window);
