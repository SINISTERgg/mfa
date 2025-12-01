import { useRef } from "react";
import "./OTPInput.css";

function OTPInput({ value, onChange, length = 6 }) {
  const inputsRef = useRef([]);

  const safe = (value || "").padEnd(length, " ");
  const digits = safe.split("").slice(0, length);

  const handleChange = (index, val) => {
    const d = val.replace(/[^0-9]/g, "").slice(0, 1);
    const arr = digits.slice();
    arr[index] = d;
    const next = arr.join("").trimEnd();
    onChange(next);

    if (d && index < length - 1) {
      inputsRef.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === "Backspace" && !digits[index].trim() && index > 0) {
      inputsRef.current[index - 1]?.focus();
    }
  };

  return (
    <div className="otp-input-root">
      {digits.map((d, i) => (
        <input
          key={i}
          ref={(el) => (inputsRef.current[i] = el)}
          className="otp-box"
          type="text"
          inputMode="numeric"
          maxLength={1}
          value={d.trim()}
          onChange={(e) => handleChange(i, e.target.value)}
          onKeyDown={(e) => handleKeyDown(i, e)}
          autoComplete={i === 0 ? "one-time-code" : "off"}
        />
      ))}
    </div>
  );
}

export default OTPInput;
