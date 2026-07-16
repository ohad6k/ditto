import type { Env } from "./contracts";

export default {
  async fetch(): Promise<Response> {
    return Response.json(
      { status: "not-configured" },
      { status: 503 },
    );
  },
} satisfies ExportedHandler<Env>;
