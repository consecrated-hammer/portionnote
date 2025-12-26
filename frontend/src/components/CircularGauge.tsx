import { useEffect, useRef, useState } from "react";

interface CircularGaugeProps {
  Value: number;
  Max: number;
  Label: string;
  Color: string;
  Size?: "small" | "large";
  ShowSubtext?: boolean;
}

export const CircularGauge = ({ 
  Value, 
  Max, 
  Label, 
  Color,
  Size = "large",
  ShowSubtext = true 
}: CircularGaugeProps) => {
  const CanvasRef = useRef<HTMLCanvasElement>(null);
  const [AnimatedValue, SetAnimatedValue] = useState(0);

  const CanvasSize = Size === "large" ? 240 : 120;
  const Radius = Size === "large" ? 85 : 42;
  const LineWidth = Size === "large" ? 12 : 8;
  const Segments = 40;

  // Animate the value
  useEffect(() => {
    const Start = AnimatedValue;
    const End = Value;
    const Duration = 800; // ms
    const StartTime = performance.now();

    const Animate = (CurrentTime: number) => {
      const Elapsed = CurrentTime - StartTime;
      const Progress = Math.min(Elapsed / Duration, 1);
      
      // Ease out cubic
      const EasedProgress = 1 - Math.pow(1 - Progress, 3);
      const Current = Start + (End - Start) * EasedProgress;
      
      SetAnimatedValue(Current);

      if (Progress < 1) {
        requestAnimationFrame(Animate);
      }
    };

    requestAnimationFrame(Animate);
  }, [Value]);

  // Draw the segmented gauge
  useEffect(() => {
    const Canvas = CanvasRef.current;
    if (!Canvas) return;

    const Ctx = Canvas.getContext("2d");
    if (!Ctx) return;

    const DPR = window.devicePixelRatio || 1;
    Canvas.width = CanvasSize * DPR;
    Canvas.height = CanvasSize * DPR;
    Canvas.style.width = `${CanvasSize}px`;
    Canvas.style.height = `${CanvasSize}px`;
    Ctx.scale(DPR, DPR);

    const CenterX = CanvasSize / 2;
    const CenterY = CanvasSize / 2;

    // Clear canvas
    Ctx.clearRect(0, 0, CanvasSize, CanvasSize);

    const Progress = Math.min(AnimatedValue / Max, 1);
    const SegmentAngle = (2 * Math.PI) / Segments;
    const GapAngle = SegmentAngle * 0.15;
    const FilledSegments = Math.round(Progress * Segments);

    // Draw segments
    for (let I = 0; I < Segments; I++) {
      const StartAngle = -Math.PI / 2 + I * SegmentAngle;
      const EndAngle = StartAngle + SegmentAngle - GapAngle;
      
      Ctx.beginPath();
      Ctx.arc(CenterX, CenterY, Radius, StartAngle, EndAngle);
      Ctx.strokeStyle = I < FilledSegments ? Color : "#e8e8e8";
      Ctx.lineWidth = LineWidth;
      Ctx.lineCap = "round";
      Ctx.stroke();
    }

    if (Size === "large") {
      // Center text - value
      Ctx.font = "bold 48px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
      Ctx.fillStyle = "#333";
      Ctx.textAlign = "center";
      Ctx.textBaseline = "middle";
      const FormattedValue = Math.round(AnimatedValue).toLocaleString();
      Ctx.fillText(FormattedValue, CenterX, CenterY - 10);

      if (ShowSubtext) {
        // Subtext - "of X Kcal"
        Ctx.font = "14px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
        Ctx.fillStyle = "#999";
        Ctx.fillText(`of ${Max.toLocaleString()} Kcal`, CenterX, CenterY + 20);
      }

      // Label above
      Ctx.font = "12px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
      Ctx.fillStyle = "#666";
      Ctx.fillText(Label, CenterX, 30);
    } else {
      // Small gauge - value in center
      Ctx.font = "bold 20px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
      Ctx.fillStyle = "#333";
      Ctx.textAlign = "center";
      Ctx.textBaseline = "middle";
      const FormattedSmallValue = Math.round(AnimatedValue).toLocaleString();
      Ctx.fillText(FormattedSmallValue, CenterX, CenterY - 5);

      if (ShowSubtext) {
        Ctx.font = "10px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
        Ctx.fillStyle = "#999";
        const FormattedMax = Math.round(Max).toLocaleString();
        Ctx.fillText(`/ ${FormattedMax}`, CenterX, CenterY + 12);
      }
    }
  }, [AnimatedValue, Max, Color, Label, Size, ShowSubtext, CanvasSize, Radius, LineWidth, Segments]);

  return (
    <div className="flex flex-col items-center gap-2">
      <canvas ref={CanvasRef} />
      {Size === "small" && (
        <div className="text-xs font-medium text-Ink/60">{Label}</div>
      )}
    </div>
  );
};
