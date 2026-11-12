import { createRoot } from "react-dom/client";
import AuthApp from "./AuthApp";
import { captureCallback } from "./oidcSession";

const callbackUrl = captureCallback();
createRoot(document.getElementById("root")!).render(
  <AuthApp callbackUrl={callbackUrl} />,
);
