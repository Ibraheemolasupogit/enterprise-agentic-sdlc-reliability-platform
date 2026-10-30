import { randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";
import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";

const port = process.env.API_PORT ?? "3000";
if (!/^\d+$/.test(port) || Number(port) < 1024 || Number(port) > 65535)
  throw new Error("Invalid local API_PORT.");
const target = `http://127.0.0.1:${port}`;
function readiness(): Plugin {
  return {
    name: "local-readiness",
    configureServer(server) {
      server.middlewares.use("/health/ready", async (_req, res) => {
        let ready = false;
        try {
          ready = (
            await fetch(`${target}/health/ready`, {
              signal: AbortSignal.timeout(1800),
            })
          ).ok;
        } catch {
          /* Dependency unavailable. */
        }
        res.statusCode = ready ? 200 : 503;
        res.setHeader("Content-Type", "application/json");
        res.end(
          JSON.stringify({
            status: ready ? "ready" : "not-ready",
            requestId: randomUUID(),
          }),
        );
      });
    },
  };
}
export default defineConfig({
  root: fileURLToPath(new URL(".", import.meta.url)),
  plugins: [react(), readiness()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": {
        target,
        timeout: 2000,
        proxyTimeout: 2000,
        configure(proxy) {
          proxy.on("error", (_error, _req, res) => {
            if ("writeHead" in res && !res.headersSent) {
              res.writeHead(503, { "Content-Type": "application/json" });
              res.end(
                JSON.stringify({
                  code: "UPSTREAM_UNAVAILABLE",
                  message: "The shop is temporarily unavailable.",
                  requestId: randomUUID(),
                }),
              );
            }
          });
        },
      },
    },
  },
  build: { outDir: "dist", emptyOutDir: true },
});
