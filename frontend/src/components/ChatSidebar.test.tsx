import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, beforeEach, afterEach } from "vitest";
import { ChatSidebar } from "@/components/ChatSidebar";
import { initialData } from "@/lib/kanban";

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn());
});

afterEach(() => {
  vi.unstubAllGlobals();
});

const mockFetch = vi.fn;

const defaultProps = {
  board: initialData,
  onBoardRefresh: vi.fn().mockResolvedValue(undefined),
};

describe("ChatSidebar", () => {
  it("renders input and empty history", () => {
    render(<ChatSidebar {...defaultProps} />);
    expect(screen.getByPlaceholderText("Ask the AI...")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /send/i })).toBeInTheDocument();
    expect(screen.getByText(/ask the ai to move/i)).toBeInTheDocument();
  });

  it("shows user message immediately on send", async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ message: "Done!", board_updated: false }),
    });

    render(<ChatSidebar {...defaultProps} />);

    const textarea = screen.getByPlaceholderText("Ask the AI...");
    await userEvent.type(textarea, "Hello AI");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    expect(screen.getByText("Hello AI")).toBeInTheDocument();
  });

  it("shows AI response after fetch resolves", async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ message: "AI replied!", board_updated: false }),
    });

    render(<ChatSidebar {...defaultProps} />);

    const textarea = screen.getByPlaceholderText("Ask the AI...");
    await userEvent.type(textarea, "Hello");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() => {
      expect(screen.getByText("AI replied!")).toBeInTheDocument();
    });
  });

  it("calls onBoardRefresh when board_updated is true", async () => {
    const onBoardRefresh = vi.fn().mockResolvedValue(undefined);
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ message: "Moved!", board_updated: true }),
    });

    render(<ChatSidebar {...defaultProps} onBoardRefresh={onBoardRefresh} />);

    const textarea = screen.getByPlaceholderText("Ask the AI...");
    await userEvent.type(textarea, "Move card");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() => {
      expect(onBoardRefresh).toHaveBeenCalledOnce();
    });
  });

  it("does not call onBoardRefresh when board_updated is false", async () => {
    const onBoardRefresh = vi.fn().mockResolvedValue(undefined);
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ message: "No changes.", board_updated: false }),
    });

    render(<ChatSidebar {...defaultProps} onBoardRefresh={onBoardRefresh} />);

    const textarea = screen.getByPlaceholderText("Ask the AI...");
    await userEvent.type(textarea, "What is on the board?");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() => {
      expect(screen.getByText("No changes.")).toBeInTheDocument();
    });
    expect(onBoardRefresh).not.toHaveBeenCalled();
  });
});
