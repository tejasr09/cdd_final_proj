import { describe, expect, it, vi } from "vitest";
import { ApiClient, ApiError } from "./api";

const config = {
  baseUrl: "http://localhost:8000/",
  userId: "user-id",
  organizationId: "organization-id",
};

describe("ApiClient", () => {
  it("sends the active local identity and uses a normalized API base URL", async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValue(
        new Response(
          JSON.stringify({ items: [], limit: 100, offset: 0, total: 0 }),
          { status: 200 },
        ),
      );
    const client = new ApiClient(config, fetcher);

    await client.listEntities();

    expect(fetcher).toHaveBeenCalledOnce();
    const [url, init] = fetcher.mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/v1/entities?limit=100");
    expect(new Headers(init?.headers).get("X-Local-User-ID")).toBe("user-id");
    expect(new Headers(init?.headers).get("X-Active-Organization-ID")).toBe(
      "organization-id",
    );
  });

  it("serializes state-changing requests as JSON", async () => {
    const created = { id: "entity-id", name: "Library" };
    const fetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValue(
        new Response(JSON.stringify(created), { status: 201 }),
      );
    const client = new ApiClient(config, fetcher);

    await expect(
      client.createEntity({ name: "Library", entity_type: "resource" }),
    ).resolves.toEqual(created);

    const [, init] = fetcher.mock.calls[0];
    expect(init?.method).toBe("POST");
    expect(new Headers(init?.headers).get("Content-Type")).toBe(
      "application/json",
    );
    expect(init?.body).toBe(
      JSON.stringify({ name: "Library", entity_type: "resource" }),
    );
  });

  it("preserves API validation details and request IDs", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(
        JSON.stringify({
          error: {
            code: "validation_error",
            message: "The request could not be validated.",
            details: [
              {
                field: "body.weight",
                message: "Input should be less than or equal to 1",
                code: "less_than_equal",
              },
            ],
            request_id: "request-123",
          },
        }),
        { status: 422, headers: { "X-Request-ID": "request-123" } },
      ),
    );
    const client = new ApiClient(config, fetcher);

    await expect(
      client.createEntity({ name: "bad", entity_type: "resource" }),
    ).rejects.toMatchObject({
      name: "ApiError",
      status: 422,
      code: "validation_error",
      requestId: "request-123",
      message: expect.stringContaining("body.weight"),
    } satisfies Partial<ApiError>);
  });
});
