export default function Logo() {
  return (
    <div className="brand">
      <svg
        width="26"
        height="26"
        viewBox="0 0 26 26"
        fill="none"
      >
        <path
          d="M13 1L23 7V19L13 25L3 19V7L13 1Z"
          stroke="#15c1af"
          strokeWidth="1.4"
        />

        <path
          d="M13 7L18 10V16L13 19L8 16V10L13 7Z"
          stroke="#f0a838"
          strokeWidth="1.4"
        />
      </svg>

      <div className="brand-name">
        ask<span>MNIT</span>
      </div>
    </div>
  );
}