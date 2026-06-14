import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import RagIndicator from "../RagIndicator.jsx";

describe("RagIndicator", () => {
  it("renders the rate when provided", () => {
    render(<RagIndicator status="GREEN" rate={92.5} />);
    expect(screen.getByText("92.5%")).toBeInTheDocument();
  });

  it("renders without a rate", () => {
    const { container } = render(<RagIndicator status="RED" />);
    // dot is always present
    expect(container.querySelector("span")).toBeTruthy();
  });
});
