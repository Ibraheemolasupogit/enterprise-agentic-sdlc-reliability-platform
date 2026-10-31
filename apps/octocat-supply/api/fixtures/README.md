# Public, non-live test vector

`rfc7515-rsa.json` is the published RSA JWK in
[RFC 7515 Appendix A.2.1](https://www.rfc-editor.org/rfc/rfc7515#appendix-A.2.1).
It is already public test material, not a generated credential or an account key.
Only deterministic test tokens use it; production accepts keys exclusively from
the explicitly configured HTTPS JWKS. Never register this key with a real provider.

Copyright (c) 2015 IETF Trust and the persons identified as the document authors.
RFC 7515 is subject to the [IETF Trust Legal Provisions](https://trustee.ietf.org/documents/trust-legal-provisions/).
Code Components are provided under the Simplified BSD License without warranty;
the applicable terms must accompany redistribution of this vector. The project
MIT license does not replace those terms.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
