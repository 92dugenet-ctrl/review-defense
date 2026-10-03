import { MuseScene } from "../MuseScene";
import { homeFaqs } from "./HomeData";

/**
 * Presents the public FAQ using the shared Muse scene layout.
 * The first item is expanded by default to make the section immediately useful.
 */
export function HomeFaq() {
  return (
    <MuseScene id="faq">
      <div className="narrow">
        <div className="eyebrow">FAQ</div>
        <h2>Comment Review Defense fonctionne ?</h2>

        <div className="faq">
          {homeFaqs.map(([question, answer], index) => (
            <details key={question} open={index === 0}>
              <summary>{question}</summary>
              <p>{answer}</p>
            </details>
          ))}
        </div>
      </div>
    </MuseScene>
  );
}
