export default function GridBackground() {
  return (
    <svg
      className="grid-background"
      width="100%"
      height="320"
      viewBox="0 0 900 320"
      preserveAspectRatio="xMidYMin slice"
    >
      <defs>
        <pattern
          id="jaali"
          width="60"
          height="60"
          patternUnits="userSpaceOnUse"
        >
          <path
            d="M30 4 L56 30 L30 56 L4 30 Z"
            fill="none"
            stroke="#2a2d32"
            strokeWidth="1"
          />

          <circle
            cx="30"
            cy="30"
            r="2.2"
            fill="#15c1af"
            opacity="0.5"
          />
        </pattern>
      </defs>

      <rect
        width="900"
        height="320"
        fill="url(#jaali)"
      />
    </svg>
  );
}