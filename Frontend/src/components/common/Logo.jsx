export default function Logo() {
  return (
    <div
      className="
        flex
        items-center
        gap-3
      "
    >
      <svg
        width="26"
        height="26"
        viewBox="0 0 26 26"
        fill="none"
      >
        <path
          d="M13 1L23 7V19L13 25L3 19V7L13 1Z"
          stroke="#15C1AF"
          strokeWidth="1.4"
        />

        <path
          d="M13 7L18 10V16L13 19L8 16V10L13 7Z"
          stroke="#F0A838"
          strokeWidth="1.4"
        />
      </svg>

      <h1
        className="
          font-['Space_Grotesk']
          text-[15.5px]
          font-semibold
          tracking-[0.2px]
          text-[#F2F1EC]
        "
      >
        ask
        <span className="text-[#15C1AF]">
          MNIT
        </span>
      </h1>
    </div>
  );
}