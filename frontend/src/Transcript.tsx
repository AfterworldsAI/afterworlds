import type { TranscriptTurn } from "./api/client";

export default function Transcript({ turns }: { turns: TranscriptTurn[] }) {
  if (turns.length === 0) {
    return (
      <p className="transcript-empty">
        No turns yet -- say something to begin.
      </p>
    );
  }
  return (
    <div className="transcript">
      {turns.map((turn) => (
        <div key={turn.turn_id} className="transcript-turn">
          <p
            className="transcript-user-input"
            data-ooc={turn.intent_classification === "ooc"}
          >
            {turn.intent_classification === "ooc" && (
              <span className="ooc-label">OOC</span>
            )}
            {turn.user_input}
          </p>
          <p
            className="transcript-assistant-output"
            data-ooc={turn.intent_classification === "ooc"}
          >
            {turn.assistant_output}
          </p>
        </div>
      ))}
    </div>
  );
}
