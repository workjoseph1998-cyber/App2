# Interface dependencies

Cirrus Experience includes a compiled React interface. Its corresponding source and lockfile are in `frontend/`. No CDN, external font service or Node.js runtime is required on the Windows application server.

The bundled interface uses React, React DOM and Scheduler (MIT), Lucide icons (ISC), Motion / Framer Motion / Motion DOM / Motion Utils (MIT), and the Manrope and IBM Plex Mono fonts (SIL Open Font License). Their copyright and license notices are retained in `frontend/licenses/`.

Vite and Prettier are development-only tools. Python dependencies are installed separately from the pinned `requirements.lock`; their distributions retain their own license notices. This notice does not change the licenses of those dependencies or imply an application-source license.
