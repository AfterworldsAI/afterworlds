import { useEffect, useState } from "react";

import { api, ApiRequestError } from "./api/client";
import type { RpgSetupConfiguration, RpgSetupView } from "./api/client";

/**
 * ADR-015c: the RPG pre-play sequence. Everything shown is the server's
 * authoritative setup view; each control is one typed operation against the
 * displayed revision. The GM conversation itself is the ordinary turn
 * composer below; a pasted sheet is submitted as a setup turn.
 */
export default function RpgSetupPanel({
  storyId,
  refreshKey,
  disabled,
  onSubmitTurn,
  onSetupChanged,
}: {
  storyId: string;
  refreshKey: number;
  disabled: boolean;
  // Resolves true only on a confirmed delivery.
  onSubmitTurn: (text: string) => Promise<boolean>;
  onSetupChanged: () => void;
}) {
  const [view, setView] = useState<RpgSetupView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [packageUuid, setPackageUuid] = useState("");
  const [sheet, setSheet] = useState("");
  // The configuration form's draft keeps the saved configuration and
  // revision it was edited from: a refresh never silently rebases unsaved
  // edits onto a newer save (ADR-015c).
  const [draft, setDraft] = useState<ConfigurationDraft | null>(null);
  const config = draft?.values ?? null;
  const setConfig = (values: RpgSetupConfiguration) =>
    setDraft((d) => d && { ...d, values });
  // A committed save whose authoritative re-read failed: the displayed view
  // (and any GM summary in it) predates the save until a read succeeds.
  const [unrefreshedSave, setUnrefreshedSave] = useState<string | null>(null);

  function show(next: RpgSetupView) {
    setView(next);
    setUnrefreshedSave(null);
    setPackageUuid(
      next.selected_package_uuid ?? next.packages[0]?.package_uuid ?? "",
    );
    setDraft((current) =>
      next.phase === "play_configuration" &&
      current &&
      differs(current.values, current.base)
        ? current
        : {
            values: next.configuration,
            base: next.configuration,
            revision: next.configuration_revision,
          },
    );
  }

  useEffect(() => {
    api
      .getRpgSetup(storyId)
      .then((next) => {
        setError(null);
        show(next);
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Could not load setup."),
      );
  }, [storyId, refreshKey]);

  async function operate(run: () => Promise<RpgSetupView>) {
    setBusy(true);
    setError(null);
    try {
      const next = await run();
      show(next);
      onSetupChanged();
    } catch (err) {
      refused(err);
    } finally {
      setBusy(false);
    }
  }

  function refused(err: unknown) {
    const problems =
      err instanceof ApiRequestError
        ? err.apiError.detail?.problems
        : undefined;
    setError(
      (err instanceof Error ? err.message : "The setup step failed.") +
        (problems ? ` (${problems})` : ""),
    );
    // The displayed revision may be stale: re-read the authoritative view.
    api
      .getRpgSetup(storyId)
      .then(show)
      .catch(() => undefined);
  }

  function reloadAfterSave() {
    return api
      .getRpgSetup(storyId)
      .then(show)
      .catch((err) =>
        setUnrefreshedSave(
          "Your settings were saved, but the setup view could not be " +
            "reloaded" +
            (err instanceof Error ? ` (${err.message})` : "") +
            ". Reload it before asking the GM to summarize them.",
        ),
      );
  }

  async function saveConfiguration(saving: ConfigurationDraft) {
    setBusy(true);
    setError(null);
    try {
      // Every field is sent: a blank optional setting is an explicit clear
      // (null), and the base revision refuses a stale form.
      await api.submitSetup(storyId, {
        mode: "rpg",
        dice_handling: saving.values.dice_handling,
        gm_cheating: saving.values.gm_cheating,
        tone: saving.values.tone,
        session_type: saving.values.session_type,
        genre_flavor: saving.values.genre_flavor ?? null,
        house_rules: saving.values.house_rules ?? null,
        acceptable_content: saving.values.acceptable_content ?? null,
        expected_configuration_revision: saving.revision,
        schema_version: 1,
      });
    } catch (err) {
      refused(err);
      setBusy(false);
      return;
    }
    // Committed: the form keeps what was saved (no longer an unsaved edit),
    // and the next successful read adopts the authoritative configuration.
    setDraft({ ...saving, base: saving.values });
    onSetupChanged();
    await reloadAfterSave();
    setBusy(false);
  }

  if (view === null) {
    return error ? (
      <p className="form-error" role="alert">
        {error}
      </p>
    ) : (
      <p>Loading setup...</p>
    );
  }
  const locked = busy || disabled;
  const dirty = draft !== null && differs(draft.values, draft.base);
  // Unsaved edits made from an older saved configuration.
  const stale =
    dirty && draft !== null && draft.revision !== view.configuration_revision;

  return (
    <section className="rpg-setup" aria-label="RPG setup">
      <h2>RPG setup</h2>
      <p data-testid="rpg-setup-phase">Step: {PHASES[view.phase]}</p>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}

      {view.phase === "world_setup" &&
        (view.world_target ? (
          <div>
            <p>
              GM understanding: <q>{view.world_target.understanding}</q>
            </p>
            <button
              type="button"
              disabled={locked}
              onClick={() =>
                operate(() =>
                  api.confirmWorld(storyId, view.world_target!.world_revision),
                )
              }
            >
              Confirm world
            </button>
          </div>
        ) : (
          <p>Describe your world to the GM below; answer any questions.</p>
        ))}

      {view.phase === "character_creation" && (
        <div>
          <label>
            Rules Package
            <select
              value={packageUuid}
              onChange={(e) => setPackageUuid(e.target.value)}
              disabled={locked}
            >
              {view.packages.map((p) => (
                <option key={p.package_uuid} value={p.package_uuid}>
                  {p.name} ({p.system} {p.version})
                </option>
              ))}
            </select>
          </label>{" "}
          {view.selected_package_uuid === packageUuid && packageUuid ? (
            <span>Selected.</span>
          ) : (
            <button
              type="button"
              disabled={locked || !packageUuid}
              onClick={() =>
                operate(() => api.selectRulesPackage(storyId, packageUuid))
              }
            >
              Use this Rules Package
            </button>
          )}
          {view.packages.length === 0 && (
            <p className="form-error" role="alert">
              No supported, published Rules Package is available.
            </p>
          )}
          <p>
            Build your character with the GM below, or paste a completed sheet:
          </p>
          <label>
            Completed character sheet
            <textarea
              value={sheet}
              onChange={(e) => setSheet(e.target.value)}
              disabled={locked}
            />
          </label>
          <button
            type="button"
            disabled={locked || !sheet.trim()}
            onClick={async () => {
              // Kept for a retry unless the turn was confirmed delivered.
              if (await onSubmitTurn(sheet)) setSheet("");
            }}
          >
            Submit sheet
          </button>
          {view.candidate && (
            <div className="rpg-candidate">
              <h3>Character for review (revision {view.candidate.revision})</h3>
              <dl>
                {view.candidate.sheet.map((row) => (
                  <div key={row.label}>
                    <dt>{row.label}</dt>
                    <dd>{row.value}</dd>
                  </div>
                ))}
              </dl>
              {view.candidate.problems.length > 0 && (
                <ul aria-label="Outstanding problems">
                  {view.candidate.problems.map((problem) => (
                    <li key={problem}>{problem}</li>
                  ))}
                </ul>
              )}
              <button
                type="button"
                disabled={locked || view.candidate.problems.length > 0}
                onClick={() =>
                  operate(() =>
                    api.acceptCharacter(storyId, view.candidate!.revision),
                  )
                }
              >
                Accept character
              </button>
            </div>
          )}
        </div>
      )}

      {view.phase === "play_configuration" && config && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            // Save through the typed setup route; the edit invalidates any
            // earlier GM summary, so the GM is asked to summarize again.
            if (draft !== null) void saveConfiguration(draft);
          }}
        >
          <label>
            Session type
            <select
              value={config.session_type}
              onChange={(e) =>
                setConfig({
                  ...config,
                  session_type: e.target.value as typeof config.session_type,
                })
              }
            >
              <option value="short_adventure">Short adventure</option>
              <option value="campaign">Campaign</option>
              <option value="open_ended">Open-ended</option>
            </select>
          </label>
          <label>
            Tone
            <select
              value={config.tone}
              onChange={(e) =>
                setConfig({
                  ...config,
                  tone: e.target.value as typeof config.tone,
                })
              }
            >
              <option value="gritty">Gritty</option>
              <option value="balanced">Balanced</option>
              <option value="forgiving">Forgiving</option>
              <option value="danger_free">Danger-free</option>
            </select>
          </label>
          <label>
            Dice handling
            <select
              value={config.dice_handling}
              onChange={(e) =>
                setConfig({
                  ...config,
                  dice_handling: e.target.value as typeof config.dice_handling,
                })
              }
            >
              <option value="ai_rolls">AI rolls</option>
              <option value="player_rolls">Player rolls</option>
            </select>
          </label>
          <label>
            <input
              type="checkbox"
              checked={config.gm_cheating}
              onChange={(e) =>
                setConfig({ ...config, gm_cheating: e.target.checked })
              }
            />{" "}
            GM cheating (never changes recorded roll results)
          </label>
          <label>
            House rules
            <textarea
              value={config.house_rules ?? ""}
              onChange={(e) =>
                setConfig({ ...config, house_rules: e.target.value || null })
              }
            />
          </label>
          <label>
            Content boundaries
            <textarea
              value={config.acceptable_content ?? ""}
              onChange={(e) =>
                setConfig({
                  ...config,
                  acceptable_content: e.target.value || null,
                })
              }
            />
          </label>
          <button type="submit" disabled={locked || !dirty || stale}>
            Save configuration
          </button>
          {stale ? (
            <div role="alert">
              <p>
                These settings were changed elsewhere after you started editing,
                so your unsaved edits cannot be saved over them.
              </p>
              <button
                type="button"
                onClick={() =>
                  setDraft({
                    values: view.configuration,
                    base: view.configuration,
                    revision: view.configuration_revision,
                  })
                }
              >
                Discard my edits and load the saved settings
              </button>
            </div>
          ) : unrefreshedSave ? (
            <div role="status">
              <p>{unrefreshedSave}</p>
              <button
                type="button"
                disabled={locked}
                onClick={() => void reloadAfterSave()}
              >
                Reload setup
              </button>
            </div>
          ) : dirty ? (
            <p>Save your changes before confirming them.</p>
          ) : view.configuration_target ? (
            <div className="rpg-configuration-summary">
              <p>
                GM summary to confirm:{" "}
                <q>{view.configuration_target.summary}</q>
              </p>
              <button
                type="button"
                disabled={locked}
                onClick={() =>
                  operate(() =>
                    api.completeRpgSetup(
                      storyId,
                      view.configuration_target!.configuration_revision,
                    ),
                  )
                }
              >
                Complete setup
              </button>
            </div>
          ) : (
            <p>
              Ask the GM below to summarize these settings, then confirm the
              summary.
            </p>
          )}
        </form>
      )}
    </section>
  );
}

type ConfigurationDraft = {
  values: RpgSetupConfiguration;
  base: RpgSetupConfiguration;
  revision: number;
};

function differs(a: RpgSetupConfiguration, b: RpgSetupConfiguration): boolean {
  return (Object.keys(CONFIG_FIELDS) as (keyof typeof CONFIG_FIELDS)[]).some(
    (k) => (a[k] ?? null) !== (b[k] ?? null),
  );
}

const CONFIG_FIELDS = {
  dice_handling: true,
  gm_cheating: true,
  tone: true,
  session_type: true,
  genre_flavor: true,
  house_rules: true,
  acceptable_content: true,
} as const;

const PHASES: Record<RpgSetupView["phase"], string> = {
  world_setup: "1 of 3 -- world",
  character_creation: "2 of 3 -- character",
  play_configuration: "3 of 3 -- play configuration",
  complete: "complete",
};
