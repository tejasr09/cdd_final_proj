import { useEffect, useRef } from "react";

type Ripple = {
  x: number;
  y: number;
  startedAt: number;
};

function RippleBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (typeof CanvasRenderingContext2D === "undefined") {
      return;
    }

    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) {
      return;
    }

    const activeCanvas = canvas;
    const drawingContext = context;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const ripples: Ripple[] = [];
    let frame = 0;
    let width = 0;
    let height = 0;

    function resize() {
      const pixelRatio = Math.min(window.devicePixelRatio || 1, 1.4);
      width = window.innerWidth;
      height = window.innerHeight;
      activeCanvas.width = Math.round(width * pixelRatio);
      activeCanvas.height = Math.round(height * pixelRatio);
      activeCanvas.style.width = `${width}px`;
      activeCanvas.style.height = `${height}px`;
      drawingContext.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
    }

    function draw(timestamp: number) {
      drawingContext.clearRect(0, 0, width, height);
      const duration = 1050;
      const maxRadius = Math.min(420, Math.hypot(width, height) * 0.44);

      for (
        let rippleIndex = ripples.length - 1;
        rippleIndex >= 0;
        rippleIndex -= 1
      ) {
        const ripple = ripples[rippleIndex];
        const progress = (timestamp - ripple.startedAt) / duration;
        if (progress >= 1) {
          ripples.splice(rippleIndex, 1);
          continue;
        }

        for (let ring = 0; ring < 3; ring += 1) {
          const ringProgress = progress - ring * 0.16;
          if (ringProgress <= 0) {
            continue;
          }

          drawingContext.beginPath();
          drawingContext.arc(
            ripple.x,
            ripple.y,
            10 + ringProgress * maxRadius,
            0,
            Math.PI * 2,
          );
          drawingContext.strokeStyle =
            ring === 0
              ? `rgba(157, 177, 255, ${(1 - ringProgress) * 0.42})`
              : `rgba(126, 117, 255, ${(1 - ringProgress) * 0.24})`;
          drawingContext.lineWidth = ring === 0 ? 1.6 : 1;
          drawingContext.stroke();
        }
      }

      if (ripples.length > 0) {
        frame = window.requestAnimationFrame(draw);
      } else {
        frame = 0;
      }
    }

    function startFrame() {
      if (!frame && !reducedMotion.matches) {
        frame = window.requestAnimationFrame(draw);
      }
    }

    function addRipple(event: PointerEvent) {
      if (reducedMotion.matches || event.button !== 0 || !event.isPrimary) {
        return;
      }

      ripples.push({
        x: event.clientX,
        y: event.clientY,
        startedAt: performance.now(),
      });
      if (ripples.length > 4) {
        ripples.shift();
      }
      startFrame();
    }

    function onMotionPreferenceChange() {
      if (reducedMotion.matches) {
        ripples.length = 0;
        if (frame) {
          window.cancelAnimationFrame(frame);
          frame = 0;
        }
        drawingContext.clearRect(0, 0, width, height);
      }
    }

    resize();
    window.addEventListener("resize", resize, { passive: true });
    window.addEventListener("pointerdown", addRipple, { passive: true });
    reducedMotion.addEventListener("change", onMotionPreferenceChange);

    return () => {
      window.removeEventListener("resize", resize);
      window.removeEventListener("pointerdown", addRipple);
      reducedMotion.removeEventListener("change", onMotionPreferenceChange);
      if (frame) {
        window.cancelAnimationFrame(frame);
      }
    };
  }, []);

  return (
    <canvas aria-hidden="true" className="ripple-background" ref={canvasRef} />
  );
}

export default RippleBackground;
