// Intentionally omit error messages, stacks, steps, URLs and attachments.
export default class OidcReporter {
  onTestEnd(test, result) {
    const ids = test.title.match(/P\d{2}/g) ?? [];
    const line = result.error?.stack?.match(/auth\.spec\.ts:(\d+):\d+/)?.[1];
    const counts = test.annotations?.find(
      (a) => a.type === "oidc-counts",
    )?.description;
    console.log(
      JSON.stringify({
        cases: ids,
        outcome: result.status,
        ...(/^\d+,\d+,\d+,\d+,\d+,\d+$/.test(counts ?? "")
          ? { protocolCounts: counts }
          : {}),
        ...(line ? { line: Number(line) } : {}),
      }),
    );
  }
  onError() {
    console.log("OIDC runner failed; sensitive diagnostics were not retained.");
  }
}
