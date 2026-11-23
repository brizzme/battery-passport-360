import {describe, expect, it} from "vitest";
import {authorised} from "./basicAuth";

const header = (s: string) => "Basic " + Buffer.from(s).toString("base64");

describe("authorised", () => {
  it("accepts exact credentials", () => expect(authorised(header("demo:s3cret:x"), "demo", "s3cret:x")).toBe(true));
  it("rejects wrong password, wrong user, missing or non-basic headers", () => {
    expect(authorised(header("demo:nope"), "demo", "s3cret")).toBe(false);
    expect(authorised(header("other:s3cret"), "demo", "s3cret")).toBe(false);
    expect(authorised(null, "demo", "s3cret")).toBe(false);
    expect(authorised("Bearer abc", "demo", "s3cret")).toBe(false);
  });
});
