import GridBackground from "./GridBackground";
import AskBox from "./AskBox";

export default function Hero() {
  return (
    <section className="hero">
      <GridBackground />

      <div className="hero-content">
        <div className="eyebrow">
          <span className="dot"></span>
          LIVE ON CIRCULARS, ORDINANCES & CAMPUS DOCS
        </div>

        <h1 className="hero-title">
            Ask MNIT<em> anything.</em>
        </h1>

        <p className="hero-subtitle">
          Search across official MNIT documents,
          circulars, and academic resources.
        </p>

        <AskBox />
      </div>
    </section>
  );
}