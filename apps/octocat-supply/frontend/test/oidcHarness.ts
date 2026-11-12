import { vi } from "vitest";
import type { INavigator } from "oidc-client-ts";
import { OidcSession } from "../src/oidcSession";
import {
  fixtureConfig,
  OidcProviderFixture,
  type ProviderOptions,
} from "../../test/fixtures/oidc-provider";

const sessions: OidcSession[] = [];
export function session(
  storage: Storage = sessionStorage,
  navigator?: INavigator,
) {
  const result = new OidcSession(fixtureConfig, storage, navigator);
  sessions.push(result);
  return result;
}
export function closeSessions() {
  for (const s of sessions.splice(0)) s.logout();
}

export async function attempt(
  options: ProviderOptions = {},
  storage: Storage = sessionStorage,
) {
  const provider = new OidcProviderFixture();
  provider.options = options;
  const transport = vi.fn(provider.fetch);
  vi.stubGlobal("fetch", transport);
  let callback = "";
  const navigator: INavigator = {
    prepare: async () => ({
      close() {},
      navigate: async ({ url }) => {
        callback = provider.authorize(url);
        return { url };
      },
    }),
    callback: async () => {},
  };
  const outgoing = session(storage, navigator);
  await outgoing.signin();
  return {
    provider,
    transport,
    outgoing,
    callback,
    incoming: session(storage),
  };
}
