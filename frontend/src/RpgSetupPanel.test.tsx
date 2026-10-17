import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiRequestError } from "./api/client";
import type { RpgSetupView } from "./api/client";
import RpgSetupPanel from "./RpgSetupPanel";

const mocks = vi.hoisted(() => ({
  getRpgSetup: vi.fn(),
  confirmWorld: vi.fn(),
  selectRulesPackage: vi.fn(),
  acceptCharacter: vi.fn(),
  completeRpgSetup: vi.fn(),
  submitSetup: vi.fn(),
}));

vi.mock("./api/client", async () => {
  const actual =
    await vi.importActual<typeof import("./api/client")>("./api/client");
  return { ...actual, api: mocks };
});

const STORY = "11111111-1111-1111-1111-111111111111";
const PKG = "1299484e-c72d-509b-bd8d-d0169ee1f8d2";

function view(overrides: Partial<RpgSetupView>): RpgSetupView {
  return {
    phase: "world_setup",
    play_status: "setup",
    world_revision: 0,
    world_target: null,
    packages: [],
    selected_package_uuid: null,
    candidate: null,
    character_accepted: false,
    configuration_revision: 0,
    configuration_target: null,
    configuration: {
      dice_handling: "ai_rolls",
      gm_cheating: true,
      tone: "balanced",
      session_type: "open_ended",
      genre_flavor: null,
      house_rules: null,
      acceptable_content: null,
      schema_version: 1,
    },
    schema_version: 1,
    ...overrides,
  };
}

function renderPanel(
  onSubmitTurn = vi.fn().mockResolvedValue(true),
  onSetupChanged = vi.fn(),
) {
  render(
    <RpgSetupPanel
      storyId={STORY}
      refreshKey={0}
      disabled={false}
      onSubmitTurn={onSubmitTurn}
      onSetupChanged={onSetupChanged}
    />,
  );
  return { onSubmitTurn, onSetupChanged };
}

describe("RpgSetupPanel (ADR-015c)", () => {
  beforeEach(() => vi.clearAllMocks());

  it("confirms the world against the displayed revision only", async () => {
    mocks.getRpgSetup.mockResolvedValue(
      view({
        world_revision: 3,
        world_target: {
          turn_id: "22222222-2222-2222-2222-222222222222",
          world_revision: 3,
          understanding: "An archipelago of lighthouses.",
          schema_version: 1,
        },
      }),
    );
    mocks.confirmWorld.mockResolvedValue(view({ phase: "character_creation" }));
    const { onSetupChanged } = renderPanel();
    fireEvent.click(
      await screen.findByRole("button", { name: "Confirm world" }),
    );
    await waitFor(() =>
      expect(mocks.confirmWorld).toHaveBeenCalledWith(STORY, 3),
    );
    expect(onSetupChanged).toHaveBeenCalled();
  });

  it("selects a package, submits a pasted sheet as a turn and accepts only a problem-free candidate", async () => {
    const candidate = {
      revision: 4,
      path: "completed_sheet" as const,
      sheet: [
        { label: "Classes", value: "wizard 1", schema_version: 1 as const },
      ],
      unresolved: [],
      problems: ["missing_state at ability_scores: not recorded"],
      schema_version: 1 as const,
    };
    mocks.getRpgSetup.mockResolvedValue(
      view({
        phase: "character_creation",
        packages: [
          {
            package_uuid: PKG,
            name: "SRD",
            system: "d20",
            version: "5.2.1",
            schema_version: 1,
          },
        ],
        candidate,
      }),
    );
    mocks.selectRulesPackage.mockResolvedValue(
      view({
        phase: "character_creation",
        packages: [
          {
            package_uuid: PKG,
            name: "SRD",
            system: "d20",
            version: "5.2.1",
            schema_version: 1,
          },
        ],
        selected_package_uuid: PKG,
        candidate: { ...candidate, revision: 5, problems: [] },
      }),
    );
    mocks.acceptCharacter.mockResolvedValue(
      view({ phase: "play_configuration" }),
    );
    const { onSubmitTurn } = renderPanel();

    expect(
      await screen.findByRole("button", { name: "Accept character" }),
    ).toBeDisabled();
    expect(screen.getByText(/ability_scores/)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Completed character sheet"), {
      target: { value: "Wizard 1, Elf, Sage" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Submit sheet" }));
    expect(onSubmitTurn).toHaveBeenCalledWith("Wizard 1, Elf, Sage");

    fireEvent.click(
      screen.getByRole("button", { name: "Use this Rules Package" }),
    );
    await waitFor(() =>
      expect(mocks.selectRulesPackage).toHaveBeenCalledWith(STORY, PKG),
    );
    const accept = await screen.findByRole("button", {
      name: "Accept character",
    });
    await waitFor(() => expect(accept).toBeEnabled());
    fireEvent.click(accept);
    await waitFor(() =>
      expect(mocks.acceptCharacter).toHaveBeenCalledWith(STORY, 5),
    );
  });

  it("saves an edited configuration, then confirms only the GM's summary at its revision", async () => {
    const summarized = view({
      phase: "play_configuration",
      configuration_revision: 2,
      configuration_target: {
        turn_id: "33333333-3333-3333-3333-333333333333",
        configuration_revision: 2,
        configuration: { ...view({}).configuration, tone: "gritty" },
        summary: "Gritty, open-ended, AI rolls, GM cheating on.",
        schema_version: 1,
      },
      configuration: { ...view({}).configuration, tone: "gritty" },
    });
    mocks.getRpgSetup.mockResolvedValue(view({ phase: "play_configuration" }));
    mocks.submitSetup.mockResolvedValue({});
    mocks.completeRpgSetup.mockResolvedValue(
      view({ phase: "complete", play_status: "in_play" }),
    );
    renderPanel();

    // No GM summary yet: nothing can be completed.
    expect(
      await screen.findByText(/Ask the GM below to summarize/),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Complete setup" })).toBeNull();

    // An unsaved edit must be saved first (it invalidates any summary).
    mocks.getRpgSetup.mockResolvedValue(
      view({
        phase: "play_configuration",
        configuration_revision: 1,
        configuration: { ...view({}).configuration, tone: "gritty" },
      }),
    );
    fireEvent.change(screen.getByLabelText("Tone"), {
      target: { value: "gritty" },
    });
    expect(screen.getByText(/Save your changes/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Save configuration" }));
    await waitFor(() =>
      expect(mocks.submitSetup).toHaveBeenCalledWith(
        STORY,
        expect.objectContaining({
          mode: "rpg",
          tone: "gritty",
          expected_configuration_revision: 0,
        }),
      ),
    );
    expect(mocks.completeRpgSetup).not.toHaveBeenCalled();

    // The GM's delivered summary is what Complete setup confirms.
    mocks.getRpgSetup.mockResolvedValue(summarized);
    cleanup();
    renderPanel();
    expect(await screen.findByText(/Gritty, open-ended/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Complete setup" }));
    await waitFor(() =>
      expect(mocks.completeRpgSetup).toHaveBeenCalledWith(STORY, 2),
    );
  });

  it("refuses an unrefreshed stale form and lets the Sojourner reload the saved settings", async () => {
    // Codex R1 re-review P1: another tab saved after this form loaded.
    mocks.getRpgSetup.mockResolvedValue(view({ phase: "play_configuration" }));
    renderPanel();
    fireEvent.change(await screen.findByLabelText("Tone"), {
      target: { value: "gritty" },
    });
    mocks.submitSetup.mockRejectedValue(
      new ApiRequestError(409, {
        error_code: "setup_state_conflict",
        message: "the configuration changed",
        detail: null,
        schema_version: 1,
      }),
    );
    const newer = view({
      phase: "play_configuration",
      configuration_revision: 1,
      configuration: {
        ...view({}).configuration,
        dice_handling: "player_rolls",
      },
    });
    mocks.getRpgSetup.mockResolvedValue(newer);
    fireEvent.click(screen.getByRole("button", { name: "Save configuration" }));
    await waitFor(() =>
      expect(mocks.submitSetup).toHaveBeenCalledWith(
        STORY,
        expect.objectContaining({
          tone: "gritty",
          expected_configuration_revision: 0,
        }),
      ),
    );
    // The edit is kept, but not rebased onto revision 1 and not re-sendable.
    expect(await screen.findByText(/changed elsewhere/)).toBeInTheDocument();
    expect(screen.getByLabelText("Tone")).toHaveValue("gritty");
    expect(
      screen.getByRole("button", { name: "Save configuration" }),
    ).toBeDisabled();
    fireEvent.click(
      screen.getByRole("button", {
        name: "Discard my edits and load the saved settings",
      }),
    );
    expect(screen.getByLabelText("Tone")).toHaveValue("balanced");
    expect(screen.getByLabelText("Dice handling")).toHaveValue("player_rolls");
    expect(screen.queryByText(/changed elsewhere/)).toBeNull();
    expect(mocks.submitSetup).toHaveBeenCalledTimes(1);
  });

  it("does not rebase unsaved edits when a refresh brings a newer configuration", async () => {
    mocks.getRpgSetup.mockResolvedValue(view({ phase: "play_configuration" }));
    const props = {
      storyId: STORY,
      disabled: false,
      onSubmitTurn: vi.fn().mockResolvedValue(true),
      onSetupChanged: vi.fn(),
    };
    const { rerender } = render(<RpgSetupPanel {...props} refreshKey={0} />);
    fireEvent.change(await screen.findByLabelText("Tone"), {
      target: { value: "gritty" },
    });
    mocks.getRpgSetup.mockResolvedValue(
      view({
        phase: "play_configuration",
        configuration_revision: 1,
        configuration: {
          ...view({}).configuration,
          dice_handling: "player_rolls",
        },
      }),
    );
    rerender(<RpgSetupPanel {...props} refreshKey={1} />);
    expect(await screen.findByText(/changed elsewhere/)).toBeInTheDocument();
    expect(screen.getByLabelText("Tone")).toHaveValue("gritty");
    expect(screen.getByLabelText("Dice handling")).toHaveValue("ai_rolls");
    expect(
      screen.getByRole("button", { name: "Save configuration" }),
    ).toBeDisabled();
    expect(mocks.submitSetup).not.toHaveBeenCalled();
  });

  it("adopts a refreshed configuration when nothing is being edited", async () => {
    mocks.getRpgSetup.mockResolvedValue(view({ phase: "play_configuration" }));
    const props = {
      storyId: STORY,
      disabled: false,
      onSubmitTurn: vi.fn().mockResolvedValue(true),
      onSetupChanged: vi.fn(),
    };
    const { rerender } = render(<RpgSetupPanel {...props} refreshKey={0} />);
    await screen.findByLabelText("Tone");
    mocks.getRpgSetup.mockResolvedValue(
      view({
        phase: "play_configuration",
        configuration_revision: 1,
        configuration: { ...view({}).configuration, tone: "forgiving" },
      }),
    );
    rerender(<RpgSetupPanel {...props} refreshKey={1} />);
    await waitFor(() =>
      expect(screen.getByLabelText("Tone")).toHaveValue("forgiving"),
    );
    expect(screen.queryByText(/changed elsewhere/)).toBeNull();
  });

  it("sends a cleared optional setting as an explicit null", async () => {
    mocks.getRpgSetup.mockResolvedValue(
      view({
        phase: "play_configuration",
        configuration_revision: 3,
        configuration: { ...view({}).configuration, house_rules: "No crits" },
      }),
    );
    mocks.submitSetup.mockResolvedValue({});
    renderPanel();
    fireEvent.change(await screen.findByLabelText("House rules"), {
      target: { value: "" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save configuration" }));
    await waitFor(() =>
      expect(mocks.submitSetup).toHaveBeenCalledWith(
        STORY,
        expect.objectContaining({
          house_rules: null,
          expected_configuration_revision: 3,
        }),
      ),
    );
  });

  it("keeps a committed save usable and truthful when the follow-up read fails", async () => {
    // Codex R2: the save committed; only the authoritative re-read failed.
    const summarized = view({
      phase: "play_configuration",
      configuration_target: {
        turn_id: "33333333-3333-3333-3333-333333333333",
        configuration_revision: 0,
        configuration: view({}).configuration,
        summary: "Balanced, open-ended.",
        schema_version: 1,
      },
    });
    mocks.getRpgSetup.mockResolvedValueOnce(summarized);
    mocks.submitSetup.mockResolvedValue({});
    renderPanel();
    fireEvent.change(await screen.findByLabelText("Tone"), {
      target: { value: "gritty" },
    });
    mocks.getRpgSetup.mockRejectedValue(new Error("network down"));
    fireEvent.click(screen.getByRole("button", { name: "Save configuration" }));

    expect(
      await screen.findByText(/were saved, but the setup view could not be/),
    ).toBeInTheDocument();
    expect(screen.queryByRole("alert")).toBeNull(); // not reported as refused
    expect(screen.getByLabelText("Tone")).toHaveValue("gritty");
    expect(
      screen.getByRole("button", { name: "Save configuration" }),
    ).toBeDisabled();
    // The pre-save summary in the displayed view is void: no Complete.
    expect(screen.queryByRole("button", { name: "Complete setup" })).toBeNull();

    mocks.getRpgSetup.mockResolvedValue(
      view({
        phase: "play_configuration",
        configuration_revision: 1,
        configuration: { ...view({}).configuration, tone: "gritty" },
      }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Reload setup" }));
    expect(
      await screen.findByText(/Ask the GM below to summarize/),
    ).toBeInTheDocument();
    expect(screen.queryByText(/were saved, but/)).toBeNull();
    expect(screen.getByLabelText("Tone")).toHaveValue("gritty");
    expect(mocks.submitSetup).toHaveBeenCalledTimes(1);
  });

  it("keeps a pasted sheet when its turn was not delivered", async () => {
    mocks.getRpgSetup.mockResolvedValue(
      view({
        phase: "character_creation",
        packages: [
          {
            package_uuid: PKG,
            name: "SRD",
            system: "d20",
            version: "5.2.1",
            schema_version: 1,
          },
        ],
      }),
    );
    const onSubmitTurn = vi.fn().mockResolvedValueOnce(false);
    renderPanel(onSubmitTurn);
    const box = await screen.findByLabelText("Completed character sheet");
    fireEvent.change(box, { target: { value: "Wizard 1, Elf, Sage" } });
    fireEvent.click(screen.getByRole("button", { name: "Submit sheet" }));
    await waitFor(() => expect(onSubmitTurn).toHaveBeenCalledTimes(1));
    expect(box).toHaveValue("Wizard 1, Elf, Sage"); // kept for a retry
    onSubmitTurn.mockResolvedValueOnce(true);
    fireEvent.click(screen.getByRole("button", { name: "Submit sheet" }));
    await waitFor(() => expect(box).toHaveValue(""));
  });

  it("shows a stale or refused step and re-reads the authoritative view", async () => {
    mocks.getRpgSetup.mockResolvedValue(
      view({
        world_revision: 1,
        world_target: {
          turn_id: "22222222-2222-2222-2222-222222222222",
          world_revision: 1,
          understanding: "A desert.",
          schema_version: 1,
        },
      }),
    );
    mocks.confirmWorld.mockRejectedValue(
      new Error("the world understanding changed"),
    );
    renderPanel();
    fireEvent.click(
      await screen.findByRole("button", { name: "Confirm world" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "the world understanding changed",
    );
    await waitFor(() => expect(mocks.getRpgSetup).toHaveBeenCalledTimes(2));
  });
});
